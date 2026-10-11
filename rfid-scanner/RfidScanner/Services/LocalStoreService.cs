using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using RfidScanner.Models;

namespace RfidScanner.Services;

/// <summary>
/// Offline-first хранилище сессий сканирования
/// </summary>
public class LocalStoreService
{
    private readonly string _dbPath;
    private readonly object _lock = new();

    public LocalStoreService()
    {
        var appData = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "PAPI", "RfidScanner");
        Directory.CreateDirectory(appData);
        _dbPath = Path.Combine(appData, "scanner.db");
        InitializeDb();
    }

    private void InitializeDb()
    {
        using var conn = new SQLiteConnection($"Data Source={_dbPath};");
        conn.Open();
        using var cmd = conn.CreateCommand();
        
        cmd.CommandText = @"
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                room_name TEXT,
                room_id INTEGER,
                started_at TEXT,
                paused_at TEXT,
                finished_at TEXT,
                state INTEGER DEFAULT 0,
                is_synced INTEGER DEFAULT 0,
                error_message TEXT
            )";
        cmd.ExecuteNonQuery();

        cmd.CommandText = @"
            CREATE TABLE IF NOT EXISTS scan_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                rfid_tag TEXT NOT NULL,
                status INTEGER NOT NULL,
                asset_name TEXT,
                inventory_number TEXT,
                scanned_at TEXT,
                manually_confirmed INTEGER DEFAULT 0,
                note TEXT
            )";
        cmd.ExecuteNonQuery();

        cmd.CommandText = "CREATE INDEX IF NOT EXISTS idx_results_session ON scan_results(session_id)";
        cmd.ExecuteNonQuery();

        // Таблица аудита
        cmd.CommandText = @"
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action INTEGER NOT NULL,
                username TEXT,
                session_id TEXT,
                room_name TEXT,
                details TEXT,
                created_at TEXT
            )";
        cmd.ExecuteNonQuery();

        cmd.CommandText = "CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_log(created_at)";
        cmd.ExecuteNonQuery();

        // Таблица ошибок считывания
        cmd.CommandText = @"
            CREATE TABLE IF NOT EXISTS scan_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                rfid_tag TEXT NOT NULL,
                error_type INTEGER NOT NULL,
                message TEXT,
                retry_count INTEGER DEFAULT 0,
                occurred_at TEXT,
                resolved INTEGER DEFAULT 0,
                resolved_by TEXT
            )";
        cmd.ExecuteNonQuery();

        // Таблица ручных вводов
        cmd.CommandText = @"
            CREATE TABLE IF NOT EXISTS manual_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                inventory_number TEXT NOT NULL,
                asset_name TEXT NOT NULL,
                asset_type TEXT,
                serial_number TEXT,
                responsible TEXT,
                note TEXT,
                entered_at TEXT,
                entered_by TEXT
            )";
        cmd.ExecuteNonQuery();

        // Таблица проверок активов (история сверок по каждому активу)
        cmd.CommandText = @"
            CREATE TABLE IF NOT EXISTS asset_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rfid_tag TEXT NOT NULL,
                inventory_number TEXT,
                asset_name TEXT,
                session_id TEXT NOT NULL,
                room_name TEXT,
                verification_status INTEGER NOT NULL,
                verified_by TEXT,
                verified_at TEXT,
                note TEXT
            )";
        cmd.ExecuteNonQuery();

        cmd.CommandText = "CREATE INDEX IF NOT EXISTS idx_verifications_asset ON asset_verifications(rfid_tag, verified_at)";
        cmd.ExecuteNonQuery();
        cmd.CommandText = "CREATE INDEX IF NOT EXISTS idx_errors_session ON scan_errors(session_id)";
        cmd.ExecuteNonQuery();
    }

    public void SaveSession(ScanSession session)
    {
        lock (_lock)
        {
            using var conn = new SQLiteConnection($"Data Source={_dbPath};");
            conn.Open();
            using var cmd = conn.CreateCommand();

            // Сохраняем сессию
            cmd.CommandText = @"
                INSERT OR REPLACE INTO sessions 
                (id, room_name, room_id, started_at, paused_at, finished_at, state, is_synced)
                VALUES (@id, @roomName, @roomId, @started, @paused, @finished, @state, 0)";
            cmd.Parameters.AddWithValue("@id", session.Id);
            cmd.Parameters.AddWithValue("@roomName", session.RoomName);
            cmd.Parameters.AddWithValue("@roomId", session.RoomId);
            cmd.Parameters.AddWithValue("@started", session.StartedAt.ToString("o"));
            cmd.Parameters.AddWithValue("@paused", (object)(session.PausedAt?.ToString("o") ?? "") ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@finished", (object)(session.FinishedAt?.ToString("o") ?? "") ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@state", (int)session.State);
            cmd.ExecuteNonQuery();

            // Сохраняем результаты
            cmd.CommandText = "DELETE FROM scan_results WHERE session_id = @sessionId";
            cmd.Parameters.Clear();
            cmd.Parameters.AddWithValue("@sessionId", session.Id);
            cmd.ExecuteNonQuery();

            foreach (var result in session.Results)
            {
                cmd.CommandText = @"
                    INSERT INTO scan_results 
                    (session_id, rfid_tag, status, asset_name, inventory_number, scanned_at, manually_confirmed, note)
                    VALUES (@sid, @tag, @status, @name, @inv, @time, @manual, @note)";
                cmd.Parameters.Clear();
                cmd.Parameters.AddWithValue("@sid", session.Id);
                cmd.Parameters.AddWithValue("@tag", result.RfidTag);
                cmd.Parameters.AddWithValue("@status", (int)result.Status);
                cmd.Parameters.AddWithValue("@name", result.AssetName ?? (object)DBNull.Value);
                cmd.Parameters.AddWithValue("@inv", result.InventoryNumber ?? (object)DBNull.Value);
                cmd.Parameters.AddWithValue("@time", result.ScannedAt.ToString("o"));
                cmd.Parameters.AddWithValue("@manual", result.ManuallyConfirmed ? 1 : 0);
                cmd.Parameters.AddWithValue("@note", (object?)result.Note ?? DBNull.Value);
                cmd.ExecuteNonQuery();
            }
        }
    }

    public ScanSession? LoadSession(string sessionId)
    {
        lock (_lock)
        {
            using var conn = new SQLiteConnection($"Data Source={_dbPath};");
            conn.Open();
            using var cmd = conn.CreateCommand();

            cmd.CommandText = "SELECT * FROM sessions WHERE id = @id";
            cmd.Parameters.AddWithValue("@id", sessionId);
            using var reader = cmd.ExecuteReader();
            
            if (!reader.Read())
                return null;

            var session = new ScanSession
            {
                Id = reader["id"].ToString()!,
                RoomName = reader["room_name"]?.ToString() ?? "",
                RoomId = Convert.ToInt32(reader["room_id"]),
                StartedAt = DateTime.Parse(reader["started_at"].ToString()!),
                PausedAt = reader["paused_at"] != DBNull.Value ? DateTime.Parse(reader["paused_at"].ToString()!) : null,
                FinishedAt = reader["finished_at"] != DBNull.Value ? DateTime.Parse(reader["finished_at"].ToString()!) : null,
                State = (SessionState)Convert.ToInt32(reader["state"])
            };

            // Загружаем результаты
            cmd.CommandText = "SELECT * FROM scan_results WHERE session_id = @id ORDER BY scanned_at";
            cmd.Parameters.Clear();
            cmd.Parameters.AddWithValue("@id", sessionId);
            
            using var resultsReader = cmd.ExecuteReader();
            while (resultsReader.Read())
            {
                session.Results.Add(new ScanResultItem
                {
                    RfidTag = resultsReader["rfid_tag"].ToString()!,
                    Status = (ScanAssetStatus)Convert.ToInt32(resultsReader["status"]),
                    AssetName = resultsReader["asset_name"]?.ToString(),
                    InventoryNumber = resultsReader["inventory_number"]?.ToString(),
                    ScannedAt = DateTime.Parse(resultsReader["scanned_at"].ToString()!),
                    ManuallyConfirmed = Convert.ToBoolean(resultsReader["manually_confirmed"]),
                    Note = resultsReader["note"]?.ToString()
                });
            }

            session.SeenTags = session.Results.Select(r => r.RfidTag).ToHashSet();
            return session;
        }
    }

    public List<ScanSession> GetUnsyncedSessions()
    {
        lock (_lock)
        {
            using var conn = new SQLiteConnection($"Data Source={_dbPath};");
            conn.Open();
            using var cmd = conn.CreateCommand();
            
            cmd.CommandText = "SELECT DISTINCT id FROM sessions WHERE is_synced = 0";
            var ids = new List<string>();
            using var reader = cmd.ExecuteReader();
            while (reader.Read())
                ids.Add(reader["id"].ToString()!);

            return ids.Select(id => LoadSession(id)).Where(s => s != null).ToList()!;
        }
    }

    public void MarkSynced(string sessionId)
    {
        lock (_lock)
        {
            using var conn = new SQLiteConnection($"Data Source={_dbPath};");
            conn.Open();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "UPDATE sessions SET is_synced = 1 WHERE id = @id";
            cmd.Parameters.AddWithValue("@id", sessionId);
            cmd.ExecuteNonQuery();
        }
    }

    public int GetPendingCount()
    {
        lock (_lock)
        {
            using var conn = new SQLiteConnection($"Data Source={_dbPath};");
            conn.Open();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT COUNT(*) FROM sessions WHERE is_synced = 0";
            return Convert.ToInt32(cmd.ExecuteScalar());
        }
    }

    // ==================== Аудит ====================

    public void LogAudit(AuditRecord record)
    {
        lock (_lock)
        {
            using var conn = new SQLiteConnection($"Data Source={_dbPath};");
            conn.Open();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"
                INSERT INTO audit_log 
                (action, username, session_id, room_name, details, created_at)
                VALUES (@action, @user, @session, @room, @details, @time)";
            cmd.Parameters.AddWithValue("@action", (int)record.Action);
            cmd.Parameters.AddWithValue("@user", (object?)record.Username ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@session", (object?)record.SessionId ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@room", (object?)record.RoomName ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@details", (object?)record.Details ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@time", record.CreatedAt.ToString("o"));
            cmd.ExecuteNonQuery();
        }
    }

    public List<AuditRecord> GetAuditHistory(int limit = 100)
    {
        lock (_lock)
        {
            using var conn = new SQLiteConnection($"Data Source={_dbPath};");
            conn.Open();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"
                SELECT * FROM audit_log 
                ORDER BY created_at DESC 
                LIMIT @limit";
            cmd.Parameters.AddWithValue("@limit", limit);
            
            var records = new List<AuditRecord>();
            using var reader = cmd.ExecuteReader();
            while (reader.Read())
            {
                records.Add(new AuditRecord
                {
                    Id = Convert.ToInt64(reader["id"]),
                    Action = (AuditAction)Convert.ToInt32(reader["action"]),
                    Username = reader["username"]?.ToString(),
                    SessionId = reader["session_id"]?.ToString(),
                    RoomName = reader["room_name"]?.ToString(),
                    Details = reader["details"]?.ToString(),
                    CreatedAt = DateTime.Parse(reader["created_at"].ToString()!)
                });
            }
            return records;
        }
    }

    // ==================== Ошибки считывания ====================

    public void SaveScanError(ScanErrorRecord error)
    {
        lock (_lock)
        {
            using var conn = new SQLiteConnection($"Data Source={_dbPath};");
            conn.Open();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"
                INSERT INTO scan_errors 
                (session_id, rfid_tag, error_type, message, retry_count, occurred_at, resolved, resolved_by)
                VALUES (@sid, @tag, @etype, @msg, @retries, @time, @resolved, @resolvedBy)";
            cmd.Parameters.AddWithValue("@sid", error.RfidTag);
            cmd.Parameters.AddWithValue("@tag", error.RfidTag);
            cmd.Parameters.AddWithValue("@etype", (int)error.ErrorType);
            cmd.Parameters.AddWithValue("@msg", (object?)error.Message ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@retries", error.RetryCount);
            cmd.Parameters.AddWithValue("@time", error.OccurredAt.ToString("o"));
            cmd.Parameters.AddWithValue("@resolved", error.IsResolved ? 1 : 0);
            cmd.Parameters.AddWithValue("@resolvedBy", (object?)error.ResolvedBy ?? DBNull.Value);
            cmd.ExecuteNonQuery();
        }
    }

    public List<ScanErrorRecord> GetUnresolvedErrors(string sessionId)
    {
        lock (_lock)
        {
            using var conn = new SQLiteConnection($"Data Source={_dbPath};");
            conn.Open();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"
                SELECT * FROM scan_errors 
                WHERE session_id = @sid AND resolved = 0 
                ORDER BY occurred_at DESC";
            cmd.Parameters.AddWithValue("@sid", sessionId);
            
            var errors = new List<ScanErrorRecord>();
            using var reader = cmd.ExecuteReader();
            while (reader.Read())
            {
                errors.Add(new ScanErrorRecord
                {
                    RfidTag = reader["rfid_tag"].ToString()!,
                    ErrorType = (ScanErrorType)Convert.ToInt32(reader["error_type"]),
                    Message = reader["message"]?.ToString(),
                    RetryCount = Convert.ToInt32(reader["retry_count"]),
                    OccurredAt = DateTime.Parse(reader["occurred_at"].ToString()!),
                    IsResolved = Convert.ToBoolean(reader["resolved"]),
                    ResolvedBy = reader["resolved_by"]?.ToString()
                });
            }
            return errors;
        }
    }

    public void ResolveScanError(string sessionId, string rfidTag, string resolvedBy)
    {
        lock (_lock)
        {
            using var conn = new SQLiteConnection($"Data Source={_dbPath};");
            conn.Open();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"
                UPDATE scan_errors 
                SET resolved = 1, resolved_by = @resolvedBy 
                WHERE session_id = @sid AND rfid_tag = @tag AND resolved = 0";
            cmd.Parameters.AddWithValue("@sid", sessionId);
            cmd.Parameters.AddWithValue("@tag", rfidTag);
            cmd.Parameters.AddWithValue("@resolvedBy", resolvedBy);
            cmd.ExecuteNonQuery();
        }
    }

    // ==================== Ручные вводы ====================

    public void SaveManualEntry(ManualAssetEntry entry, string sessionId)
    {
        lock (_lock)
        {
            using var conn = new SQLiteConnection($"Data Source={_dbPath};");
            conn.Open();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"
                INSERT INTO manual_entries 
                (session_id, inventory_number, asset_name, asset_type, serial_number, responsible, note, entered_at, entered_by)
                VALUES (@sid, @inv, @name, @type, @serial, @resp, @note, @time, @user)";
            cmd.Parameters.AddWithValue("@sid", sessionId);
            cmd.Parameters.AddWithValue("@inv", entry.InventoryNumber);
            cmd.Parameters.AddWithValue("@name", entry.AssetName);
            cmd.Parameters.AddWithValue("@type", (object?)entry.AssetType ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@serial", (object?)entry.SerialNumber ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@resp", (object?)entry.Responsible ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@note", (object?)entry.Note ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@time", entry.EnteredAt.ToString("o"));
            cmd.Parameters.AddWithValue("@user", entry.EnteredBy);
            cmd.ExecuteNonQuery();
        }
    }

    public List<ManualAssetEntry> GetManualEntries(string sessionId)
    {
        lock (_lock)
        {
            using var conn = new SQLiteConnection($"Data Source={_dbPath};");
            conn.Open();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"
                SELECT * FROM manual_entries 
                WHERE session_id = @sid ORDER BY entered_at DESC";
            cmd.Parameters.AddWithValue("@sid", sessionId);
            
            var entries = new List<ManualAssetEntry>();
            using var reader = cmd.ExecuteReader();
            while (reader.Read())
            {
                entries.Add(new ManualAssetEntry
                {
                    InventoryNumber = reader["inventory_number"].ToString()!,
                    AssetName = reader["asset_name"].ToString()!,
                    AssetType = reader["asset_type"]?.ToString(),
                    SerialNumber = reader["serial_number"]?.ToString(),
                    Responsible = reader["responsible"]?.ToString(),
                    Note = reader["note"]?.ToString(),
                    EnteredAt = DateTime.Parse(reader["entered_at"].ToString()!),
                    EnteredBy = reader["entered_by"]?.ToString() ?? ""
                });
            }
            return entries;
        }
    }

    // ==================== История проверок активов ====================

    public void SaveAssetVerification(ScanResultItem result, string verifiedBy)
    {
        lock (_lock)
        {
            using var conn = new SQLiteConnection($"Data Source={_dbPath};");
            conn.Open();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"
                INSERT INTO asset_verifications 
                (rfid_tag, inventory_number, asset_name, session_id, room_name, verification_status, verified_by, verified_at, note)
                VALUES (@tag, @inv, @name, @sid, @room, @status, @user, @time, @note)";
            cmd.Parameters.AddWithValue("@tag", result.RfidTag);
            cmd.Parameters.AddWithValue("@inv", (object?)result.InventoryNumber ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@name", (object?)result.AssetName ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@sid", result.ScannedAt.ToString("o"));
            cmd.Parameters.AddWithValue("@room", result.RoomId.ToString());
            cmd.Parameters.AddWithValue("@status", (int)result.Status);
            cmd.Parameters.AddWithValue("@user", verifiedBy);
            cmd.Parameters.AddWithValue("@time", result.ScannedAt.ToString("o"));
            cmd.Parameters.AddWithValue("@note", (object?)result.Note ?? DBNull.Value);
            cmd.ExecuteNonQuery();
        }
    }

    /// <summary>
    /// Получить историю проверок для конкретного RFID-тега
    /// </summary>
    public List<ScanResultItem> GetAssetVerificationHistory(string rfidTag, int limit = 10)
    {
        lock (_lock)
        {
            using var conn = new SQLiteConnection($"Data Source={_dbPath};");
            conn.Open();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"
                SELECT * FROM asset_verifications 
                WHERE rfid_tag = @tag 
                ORDER BY verified_at DESC 
                LIMIT @limit";
            cmd.Parameters.AddWithValue("@tag", rfidTag);
            cmd.Parameters.AddWithValue("@limit", limit);
            
            var results = new List<ScanResultItem>();
            using var reader = cmd.ExecuteReader();
            while (reader.Read())
            {
                results.Add(new ScanResultItem
                {
                    RfidTag = reader["rfid_tag"].ToString()!,
                    Status = (ScanAssetStatus)Convert.ToInt32(reader["verification_status"]),
                    AssetName = reader["asset_name"]?.ToString(),
                    InventoryNumber = reader["inventory_number"]?.ToString(),
                    ScannedAt = DateTime.Parse(reader["verified_at"].ToString()!),
                    Note = reader["note"]?.ToString()
                });
            }
            return results;
        }
    }

    /// <summary>
    /// Последняя проверка актива
    /// </summary>
    public (bool Found, ScanResultItem? LastVerification)? GetLastAssetVerification(string rfidTag)
    {
        var history = GetAssetVerificationHistory(rfidTag, 1);
        if (history.Count > 0)
            return (Found: true, LastVerification: history[0]);
        return null;
    }
}
