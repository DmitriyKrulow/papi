using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.IO;
using Newtonsoft.Json;
using RfidScanner.Models;

namespace RfidScanner.Services;

/// <summary>
/// Офлайн-очередь для отложенной синхронизации
/// Использует SQLite для хранения операций без подключения к сети
/// </summary>
public class OfflineQueueService
{
    private readonly string _dbPath;
    private readonly object _lock = new();

    public OfflineQueueService()
    {
        var appData = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "PAPI", "RfidScanner");
        Directory.CreateDirectory(appData);
        _dbPath = Path.Combine(appData, "offline_queue.db");
        InitializeDb();
    }

    private void InitializeDb()
    {
        using var conn = new SQLiteConnection($"Data Source={_dbPath};");
        conn.Open();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"
            CREATE TABLE IF NOT EXISTS queue_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                rfid_tags TEXT NOT NULL,
                inventory_id INTEGER,
                room_id INTEGER,
                department_code TEXT,
                responsible_person TEXT,
                from_room_id TEXT,
                to_room_id TEXT,
                reason TEXT,
                document_number TEXT,
                created_at TEXT NOT NULL,
                synced_at TEXT,
                is_synced INTEGER DEFAULT 0,
                error_message TEXT
            )";
        cmd.ExecuteNonQuery();
        
        cmd.CommandText = "CREATE INDEX IF NOT EXISTS idx_sync ON queue_items(is_synced, created_at)";
        cmd.ExecuteNonQuery();
    }

    public void AddItem(OfflineQueueItem item)
    {
        lock (_lock)
        {
            using var conn = new SQLiteConnection($"Data Source={_dbPath};");
            conn.Open();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"
                INSERT INTO queue_items 
                (operation_type, rfid_tags, inventory_id, room_id, department_code, 
                 responsible_person, from_room_id, to_room_id, reason, document_number, 
                 created_at, is_synced, error_message)
                VALUES (@op, @tags, @inv, @room, @dept, @resp, @from, @to, @reason, @doc, @created, 0, @err)";
            cmd.Parameters.AddWithValue("@op", item.OperationType.ToString());
            cmd.Parameters.AddWithValue("@tags", item.RfidTags);
            cmd.Parameters.AddWithValue("@inv", (object?)item.InventoryId ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@room", (object?)item.RoomId ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@dept", (object?)item.DepartmentCode ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@resp", (object?)item.ResponsiblePerson ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@from", (object?)item.FromRoomId ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@to", (object?)item.ToRoomId ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@reason", (object?)item.Reason ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@doc", (object?)item.DocumentNumber ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@created", item.CreatedAt.ToString("o"));
            cmd.Parameters.AddWithValue("@err", (object?)item.ErrorMessage ?? DBNull.Value);
            cmd.ExecuteNonQuery();
        }
    }

    public List<OfflineQueueItem> GetPendingItems()
    {
        lock (_lock)
        {
            using var conn = new SQLiteConnection($"Data Source={_dbPath};");
            conn.Open();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT * FROM queue_items WHERE is_synced = 0 ORDER BY created_at ASC";
            
            var items = new List<OfflineQueueItem>();
            using var reader = cmd.ExecuteReader();
            while (reader.Read())
            {
                items.Add(new OfflineQueueItem
                {
                    Id = Convert.ToInt64(reader["id"]),
                    OperationType = Enum.Parse<OfflineOperationType>(reader["operation_type"].ToString()!),
                    RfidTags = reader["rfid_tags"].ToString()!,
                    InventoryId = reader["inventory_id"] != DBNull.Value ? Convert.ToInt32(reader["inventory_id"]) : null,
                    RoomId = reader["room_id"] != DBNull.Value ? Convert.ToInt32(reader["room_id"]) : null,
                    DepartmentCode = reader["department_code"]?.ToString(),
                    ResponsiblePerson = reader["responsible_person"]?.ToString(),
                    FromRoomId = reader["from_room_id"]?.ToString(),
                    ToRoomId = reader["to_room_id"]?.ToString(),
                    Reason = reader["reason"]?.ToString(),
                    DocumentNumber = reader["document_number"]?.ToString(),
                    CreatedAt = DateTime.Parse(reader["created_at"].ToString()!),
                    SyncedAt = reader["synced_at"] != DBNull.Value ? DateTime.Parse(reader["synced_at"].ToString()!) : null,
                    IsSynced = Convert.ToInt32(reader["is_synced"]) == 1,
                    ErrorMessage = reader["error_message"]?.ToString()
                });
            }
            return items;
        }
    }

    public async Task<int> SyncItemsAsync(Func<List<OfflineQueueItem>, Task<bool>> syncFunc)
    {
        var pending = GetPendingItems();
        if (pending.Count == 0)
            return 0;

        var success = await syncFunc(pending);
        if (success)
        {
            MarkAsSynced(pending);
        }
        return pending.Count;
    }

    private void MarkAsSynced(List<OfflineQueueItem> items)
    {
        lock (_lock)
        {
            using var conn = new SQLiteConnection($"Data Source={_dbPath};");
            conn.Open();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "UPDATE queue_items SET is_synced = 1, synced_at = @now WHERE id IN (@ids)";
            
            foreach (var item in items)
            {
                cmd.Parameters.Clear();
                cmd.Parameters.AddWithValue("@now", DateTime.Now.ToString("o"));
                cmd.Parameters.AddWithValue("@id", item.Id);
                cmd.ExecuteNonQuery();
            }
        }
    }

    public int GetPendingCount()
    {
        lock (_lock)
        {
            using var conn = new SQLiteConnection($"Data Source={_dbPath};");
            conn.Open();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT COUNT(*) as count FROM queue_items WHERE is_synced = 0";
            return Convert.ToInt32(cmd.ExecuteScalar());
        }
    }

    public void ClearSynced()
    {
        lock (_lock)
        {
            using var conn = new SQLiteConnection($"Data Source={_dbPath};");
            conn.Open();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "DELETE FROM queue_items WHERE is_synced = 1";
            cmd.ExecuteNonQuery();
        }
    }
}
