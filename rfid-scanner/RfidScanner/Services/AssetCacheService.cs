using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Newtonsoft.Json;
using RfidScanner.Models;

namespace RfidScanner.Services;

/// <summary>
/// Кэш активов для помещения (JSON файлы)
/// </summary>
public class AssetCacheService
{
    private readonly string _dataDir;
    private readonly object _lock = new();

    public AssetCacheService()
    {
        _dataDir = @"C:\Users\Public\PAPI\RfidScanner\data";
        Directory.CreateDirectory(_dataDir);
    }

    private string FilePath(string name) => Path.Combine(_dataDir, name + ".json");

    public async Task<bool> LoadRoomAssetsAsync(int roomId, List<Asset> assets)
    {
        lock (_lock)
        {
            var data = new
            {
                RoomId = roomId,
                UpdatedAt = DateTime.Now,
                Assets = assets.Select(a => new
                {
                    a.RfidTag,
                    Name = a.Name ?? "",
                    InventoryNumber = a.InventoryNumber ?? ""
                }).ToList()
            };
            File.WriteAllText(FilePath("cache_room_" + roomId), JsonConvert.SerializeObject(data, Formatting.Indented));
            return true;
        }
    }

    public (bool Found, string AssetName, string InventoryNumber) CheckLocalCache(string rfidTag)
    {
        // Нормализация: приводим к верхнему регистру для нечувствительного сравнения
        var normalized = rfidTag.ToUpperInvariant().Trim();
        
        lock (_lock)
        {
            foreach (var file in Directory.GetFiles(_dataDir, "cache_room_*.json"))
            {
                var json = File.ReadAllText(file);
                var d = JsonConvert.DeserializeObject<RoomCacheJson>(json);
                if (d != null)
                {
                    var asset = d.Assets?.FirstOrDefault(a => 
                        !string.IsNullOrEmpty(a.RfidTag) && 
                        a.RfidTag.ToUpperInvariant().Trim() == normalized);
                    if (asset != null)
                        return (Found: true, asset.Name, asset.InventoryNumber);
                }
            }
            return (Found: false, "", "");
        }
    }

    public List<string> GetExpectedTags(int roomId)
    {
        lock (_lock)
        {
            var path = FilePath("cache_room_" + roomId);
            if (!File.Exists(path)) return new();
            
            var d = JsonConvert.DeserializeObject<RoomCacheJson>(File.ReadAllText(path));
            return d?.Assets?.Select(a => a.RfidTag).ToList() ?? new();
        }
    }

    public void MarkDeferred(string rfidTag, string note = "")
    {
        // No-op
    }

    private class RoomCacheJson
    {
        public int RoomId { get; set; }
        public DateTime UpdatedAt { get; set; }
        public List<AssetCache>? Assets { get; set; }
    }

    private class AssetCache
    {
        public string RfidTag { get; set; } = "";
        public string Name { get; set; } = "";
        public string InventoryNumber { get; set; } = "";
    }
}
