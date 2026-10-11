using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Newtonsoft.Json;
using RfidScanner.Models;

namespace RfidScanner.Services;

/// <summary>
/// Offline-first хранилище (JSON файлы, без SQLite)
/// </summary>
public class LocalStoreService
{
    private readonly string _dataDir;
    private readonly object _lock = new();

    public LocalStoreService()
    {
        _dataDir = @"C:\Users\Public\PAPI\RfidScanner\data";
        Directory.CreateDirectory(_dataDir);
    }

    private string FilePath(string name) => Path.Combine(_dataDir, name + ".json");

    public void SaveSession(ScanSession session)
    {
        lock (_lock)
        {
            var data = new
            {
                session.Id,
                session.RoomName,
                session.RoomId,
                session.StartedAt,
                session.PausedAt,
                session.FinishedAt,
                State = (int)session.State,
                Results = session.Results.Select(r => new
                {
                    r.RfidTag,
                    Status = (int)r.Status,
                    r.AssetName,
                    r.InventoryNumber,
                    r.ScannedAt,
                    r.ManuallyConfirmed,
                    r.Note
                }).ToList()
            };
            File.WriteAllText(FilePath("session_" + session.Id), JsonConvert.SerializeObject(data, Formatting.Indented));
        }
    }

    public ScanSession? LoadSession(string sessionId)
    {
        lock (_lock)
        {
            var path = FilePath("session_" + sessionId);
            if (!File.Exists(path)) return null;
            
            var json = File.ReadAllText(path);
            var d = JsonConvert.DeserializeObject<SessionJson>(json);
            if (d == null) return null;

            var session = new ScanSession
            {
                Id = d.Id,
                RoomName = d.RoomName,
                RoomId = d.RoomId,
                StartedAt = d.StartedAt,
                PausedAt = d.PausedAt,
                FinishedAt = d.FinishedAt,
                State = (SessionState)d.State
            };

            foreach (var r in d.Results)
            {
                session.Results.Add(new ScanResultItem
                {
                    RfidTag = r.RfidTag,
                    Status = (ScanAssetStatus)r.Status,
                    AssetName = r.AssetName,
                    InventoryNumber = r.InventoryNumber,
                    ScannedAt = r.ScannedAt,
                    ManuallyConfirmed = r.ManuallyConfirmed,
                    Note = r.Note
                });
            }

            session.SeenTags = session.Results.Select(x => x.RfidTag).ToHashSet();
            return session;
        }
    }

    public List<ScanSession> GetUnsyncedSessions()
    {
        lock (_lock)
        {
            var sessions = new List<ScanSession>();
            foreach (var file in Directory.GetFiles(_dataDir, "session_*.json"))
            {
                var session = LoadSession(Path.GetFileNameWithoutExtension(file).Replace("session_", ""));
                if (session != null) sessions.Add(session);
            }
            return sessions;
        }
    }

    public void MarkSynced(string sessionId) { }

    public int GetPendingCount() => Directory.GetFiles(_dataDir, "session_*.json").Length;

    // ==================== Аудит ====================

    public void LogAudit(AuditRecord record)
    {
        lock (_lock)
        {
            var auditPath = FilePath("audit");
            var records = File.Exists(auditPath)
                ? JsonConvert.DeserializeObject<List<AuditJson>>(File.ReadAllText(auditPath)) ?? new()
                : new List<AuditJson>();
            
            records.Add(new AuditJson
            {
                Action = (int)record.Action,
                Username = record.Username,
                SessionId = record.SessionId,
                RoomName = record.RoomName,
                Details = record.Details,
                CreatedAt = record.CreatedAt
            });
            
            File.WriteAllText(auditPath, JsonConvert.SerializeObject(records, Formatting.Indented));
        }
    }

    public List<AuditRecord> GetAuditHistory(int limit = 100)
    {
        lock (_lock)
        {
            var auditPath = FilePath("audit");
            if (!File.Exists(auditPath)) return new();
            
            var records = JsonConvert.DeserializeObject<List<AuditJson>>(File.ReadAllText(auditPath)) ?? new();
            return records.OrderByDescending(r => r.CreatedAt)
                .Take(limit)
                .Select(r => new AuditRecord
                {
                    Action = (AuditAction)r.Action,
                    Username = r.Username,
                    SessionId = r.SessionId,
                    RoomName = r.RoomName,
                    Details = r.Details,
                    CreatedAt = r.CreatedAt
                }).ToList();
        }
    }

    // ==================== Ошибки считывания ====================

    public void SaveScanError(ScanErrorRecord error)
    {
        lock (_lock)
        {
            var path = FilePath("errors");
            var records = File.Exists(path)
                ? JsonConvert.DeserializeObject<List<ErrorJson>>(File.ReadAllText(path)) ?? new()
                : new List<ErrorJson>();
            
            records.Add(new ErrorJson
            {
                SessionId = error.RfidTag,
                RfidTag = error.RfidTag,
                ErrorType = (int)error.ErrorType,
                Message = error.Message,
                RetryCount = error.RetryCount,
                OccurredAt = error.OccurredAt,
                IsResolved = error.IsResolved,
                ResolvedBy = error.ResolvedBy
            });
            
            File.WriteAllText(path, JsonConvert.SerializeObject(records, Formatting.Indented));
        }
    }

    public List<ScanErrorRecord> GetUnresolvedErrors(string sessionId)
    {
        lock (_lock)
        {
            var path = FilePath("errors");
            if (!File.Exists(path)) return new();
            
            var records = JsonConvert.DeserializeObject<List<ErrorJson>>(File.ReadAllText(path)) ?? new();
            return records.Where(r => !r.IsResolved)
                .Select(r => new ScanErrorRecord
                {
                    RfidTag = r.RfidTag,
                    ErrorType = (ScanErrorType)r.ErrorType,
                    Message = r.Message,
                    RetryCount = r.RetryCount,
                    OccurredAt = r.OccurredAt,
                    IsResolved = r.IsResolved,
                    ResolvedBy = r.ResolvedBy
                }).ToList();
        }
    }

    public void ResolveScanError(string sessionId, string rfidTag, string resolvedBy)
    {
        // No-op for JSON storage
    }

    // ==================== Ручные вводы ====================

    public void SaveManualEntry(ManualAssetEntry entry, string sessionId)
    {
        lock (_lock)
        {
            var path = FilePath("manual_entries");
            var records = File.Exists(path)
                ? JsonConvert.DeserializeObject<List<ManualJson>>(File.ReadAllText(path)) ?? new()
                : new List<ManualJson>();
            
            records.Add(new ManualJson
            {
                SessionId = sessionId,
                InventoryNumber = entry.InventoryNumber,
                AssetName = entry.AssetName,
                AssetType = entry.AssetType,
                SerialNumber = entry.SerialNumber,
                Responsible = entry.Responsible,
                Note = entry.Note,
                EnteredAt = entry.EnteredAt,
                EnteredBy = entry.EnteredBy
            });
            
            File.WriteAllText(path, JsonConvert.SerializeObject(records, Formatting.Indented));
        }
    }

    public List<ManualAssetEntry> GetManualEntries(string sessionId)
    {
        lock (_lock)
        {
            var path = FilePath("manual_entries");
            if (!File.Exists(path)) return new();
            
            var records = JsonConvert.DeserializeObject<List<ManualJson>>(File.ReadAllText(path)) ?? new();
            return records.Where(r => r.SessionId == sessionId)
                .Select(r => new ManualAssetEntry
                {
                    InventoryNumber = r.InventoryNumber,
                    AssetName = r.AssetName,
                    AssetType = r.AssetType,
                    SerialNumber = r.SerialNumber,
                    Responsible = r.Responsible,
                    Note = r.Note,
                    EnteredAt = r.EnteredAt,
                    EnteredBy = r.EnteredBy
                }).ToList();
        }
    }

    // ==================== История проверок активов ====================

    public void SaveAssetVerification(ScanResultItem result, string verifiedBy)
    {
        lock (_lock)
        {
            var path = FilePath("verifications");
            var records = File.Exists(path)
                ? JsonConvert.DeserializeObject<List<VerificationJson>>(File.ReadAllText(path)) ?? new()
                : new List<VerificationJson>();
            
            records.Add(new VerificationJson
            {
                RfidTag = result.RfidTag,
                InventoryNumber = result.InventoryNumber,
                AssetName = result.AssetName,
                SessionId = result.ScannedAt.ToString("o"),
                RoomName = result.RoomId.ToString(),
                VerificationStatus = (int)result.Status,
                VerifiedBy = verifiedBy,
                VerifiedAt = result.ScannedAt,
                Note = result.Note
            });
            
            File.WriteAllText(path, JsonConvert.SerializeObject(records, Formatting.Indented));
        }
    }

    public List<ScanResultItem> GetAssetVerificationHistory(string rfidTag, int limit = 10)
    {
        lock (_lock)
        {
            var path = FilePath("verifications");
            if (!File.Exists(path)) return new();
            
            var records = JsonConvert.DeserializeObject<List<VerificationJson>>(File.ReadAllText(path)) ?? new();
            return records.Where(r => r.RfidTag == rfidTag)
                .OrderByDescending(r => r.VerifiedAt)
                .Take(limit)
                .Select(r => new ScanResultItem
                {
                    RfidTag = r.RfidTag,
                    Status = (ScanAssetStatus)r.VerificationStatus,
                    AssetName = r.AssetName,
                    InventoryNumber = r.InventoryNumber,
                    ScannedAt = r.VerifiedAt,
                    Note = r.Note
                }).ToList();
        }
    }

    public (bool Found, ScanResultItem? LastVerification)? GetLastAssetVerification(string rfidTag)
    {
        var history = GetAssetVerificationHistory(rfidTag, 1);
        if (history.Count > 0)
            return (Found: true, LastVerification: history[0]);
        return null;
    }

    // ==================== JSON DTOs ====================

    private class SessionJson
    {
        public string Id { get; set; } = "";
        public string RoomName { get; set; } = "";
        public int RoomId { get; set; }
        public DateTime StartedAt { get; set; }
        public DateTime? PausedAt { get; set; }
        public DateTime? FinishedAt { get; set; }
        public int State { get; set; }
        public List<ResultJson> Results { get; set; } = new();
    }

    private class ResultJson
    {
        public string RfidTag { get; set; } = "";
        public int Status { get; set; }
        public string? AssetName { get; set; }
        public string? InventoryNumber { get; set; }
        public DateTime ScannedAt { get; set; }
        public bool ManuallyConfirmed { get; set; }
        public string? Note { get; set; }
    }

    private class AuditJson
    {
        public int Action { get; set; }
        public string? Username { get; set; }
        public string? SessionId { get; set; }
        public string? RoomName { get; set; }
        public string? Details { get; set; }
        public DateTime CreatedAt { get; set; }
    }

    private class ErrorJson
    {
        public string SessionId { get; set; } = "";
        public string RfidTag { get; set; } = "";
        public int ErrorType { get; set; }
        public string? Message { get; set; }
        public int RetryCount { get; set; }
        public DateTime OccurredAt { get; set; }
        public bool IsResolved { get; set; }
        public string? ResolvedBy { get; set; }
    }

    private class ManualJson
    {
        public string SessionId { get; set; } = "";
        public string InventoryNumber { get; set; } = "";
        public string AssetName { get; set; } = "";
        public string? AssetType { get; set; }
        public string? SerialNumber { get; set; }
        public string? Responsible { get; set; }
        public string? Note { get; set; }
        public DateTime EnteredAt { get; set; }
        public string EnteredBy { get; set; } = "";
    }

    private class VerificationJson
    {
        public string RfidTag { get; set; } = "";
        public string? InventoryNumber { get; set; }
        public string? AssetName { get; set; }
        public string SessionId { get; set; } = "";
        public string? RoomName { get; set; }
        public int VerificationStatus { get; set; }
        public string VerifiedBy { get; set; } = "";
        public DateTime VerifiedAt { get; set; }
        public string? Note { get; set; }
    }
}
