using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Newtonsoft.Json;
using RfidScanner.Models;

namespace RfidScanner.Services;

/// <summary>
/// Офлайн-очередь (JSON файлы)
/// </summary>
public class OfflineQueueService
{
    private readonly string _dataDir;
    private readonly object _lock = new();

    public OfflineQueueService()
    {
        _dataDir = @"C:\Users\Public\PAPI\RfidScanner\data";
        Directory.CreateDirectory(_dataDir);
    }

    private string FilePath(string name) => Path.Combine(_dataDir, name + ".json");

    public void AddItem(OfflineQueueItem item)
    {
        lock (_lock)
        {
            var path = FilePath("queue");
            var items = File.Exists(path)
                ? JsonConvert.DeserializeObject<List<QueueJson>>(File.ReadAllText(path)) ?? new()
                : new List<QueueJson>();
            
            items.Add(new QueueJson
            {
                Id = item.Id,
                OperationType = item.OperationType.ToString(),
                RfidTags = item.RfidTags,
                InventoryId = item.InventoryId,
                RoomId = item.RoomId,
                DepartmentCode = item.DepartmentCode,
                ResponsiblePerson = item.ResponsiblePerson,
                FromRoomId = item.FromRoomId,
                ToRoomId = item.ToRoomId,
                Reason = item.Reason,
                DocumentNumber = item.DocumentNumber,
                CreatedAt = item.CreatedAt,
                SyncedAt = item.SyncedAt,
                IsSynced = item.IsSynced,
                ErrorMessage = item.ErrorMessage
            });
            
            File.WriteAllText(path, JsonConvert.SerializeObject(items, Formatting.Indented));
        }
    }

    public List<OfflineQueueItem> GetPendingItems()
    {
        lock (_lock)
        {
            var path = FilePath("queue");
            if (!File.Exists(path)) return new();
            
            var items = JsonConvert.DeserializeObject<List<QueueJson>>(File.ReadAllText(path)) ?? new();
            return items.Where(i => !i.IsSynced)
                .Select(i => new OfflineQueueItem
                {
                    Id = i.Id,
                    OperationType = Enum.Parse<OfflineOperationType>(i.OperationType!),
                    RfidTags = i.RfidTags!,
                    InventoryId = i.InventoryId,
                    RoomId = i.RoomId,
                    DepartmentCode = i.DepartmentCode,
                    ResponsiblePerson = i.ResponsiblePerson,
                    FromRoomId = i.FromRoomId,
                    ToRoomId = i.ToRoomId,
                    Reason = i.Reason,
                    DocumentNumber = i.DocumentNumber,
                    CreatedAt = i.CreatedAt,
                    SyncedAt = i.SyncedAt,
                    IsSynced = i.IsSynced,
                    ErrorMessage = i.ErrorMessage
                }).ToList();
        }
    }

    public async Task<int> SyncItemsAsync(Func<List<OfflineQueueItem>, Task<bool>> syncFunc)
    {
        var pending = GetPendingItems();
        if (pending.Count == 0) return 0;
        var success = await syncFunc(pending);
        if (success) MarkAsSynced(pending);
        return pending.Count;
    }

    public void MarkAsSynced(List<OfflineQueueItem> items)
    {
        lock (_lock)
        {
            var path = FilePath("queue");
            if (!File.Exists(path)) return;
            var json = File.ReadAllText(path);
            var all = JsonConvert.DeserializeObject<List<QueueJson>>(json) ?? new();
            foreach (var item in items)
            {
                var q = all.FirstOrDefault(x => x.Id == item.Id);
                if (q != null)
                {
                    q.IsSynced = true;
                    q.SyncedAt = DateTime.Now;
                }
            }
            File.WriteAllText(path, JsonConvert.SerializeObject(all, Formatting.Indented));
        }
    }

    public int GetPendingCount()
    {
        lock (_lock)
        {
            var path = FilePath("queue");
            if (!File.Exists(path)) return 0;
            var items = JsonConvert.DeserializeObject<List<QueueJson>>(File.ReadAllText(path)) ?? new();
            return items.Count(i => !i.IsSynced);
        }
    }

    public void ClearSynced()
    {
        lock (_lock)
        {
            var path = FilePath("queue");
            if (!File.Exists(path)) return;
            var json = File.ReadAllText(path);
            var all = JsonConvert.DeserializeObject<List<QueueJson>>(json) ?? new();
            all.RemoveAll(i => i.IsSynced);
            File.WriteAllText(path, JsonConvert.SerializeObject(all, Formatting.Indented));
        }
    }

    private class QueueJson
    {
        public long Id { get; set; }
        public string? OperationType { get; set; }
        public string? RfidTags { get; set; }
        public int? InventoryId { get; set; }
        public int? RoomId { get; set; }
        public string? DepartmentCode { get; set; }
        public string? ResponsiblePerson { get; set; }
        public string? FromRoomId { get; set; }
        public string? ToRoomId { get; set; }
        public string? Reason { get; set; }
        public string? DocumentNumber { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime? SyncedAt { get; set; }
        public bool IsSynced { get; set; }
        public string? ErrorMessage { get; set; }
    }
}
