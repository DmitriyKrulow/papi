using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using RfidScanner.Models;

namespace RfidScanner.Services;

/// <summary>
/// Кэш активов для помещения (локально, без сети)
/// </summary>
public class AssetCacheService
{
    private readonly string _dbPath;
    private readonly object _lock = new();

    public AssetCacheService()
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
            CREATE TABLE IF NOT EXISTS asset_cache (
                rfid_tag TEXT PRIMARY KEY,
                asset_name TEXT,
                inventory_number TEXT,
                room_id INTEGER,
                last_updated TEXT,
                is_active INTEGER DEFAULT 1
            )";
        cmd.ExecuteNonQuery();

        cmd.CommandText = "CREATE INDEX IF NOT EXISTS idx_cache_room ON asset_cache(room_id, is_active)";
        cmd.ExecuteNonQuery();
    }

    /// <summary>
    /// Загрузить кэш активов для помещения
    /// </summary>
    public async Task<bool> LoadRoomAssetsAsync(int roomId, List<Asset> assets)
    {
        lock (_lock)
        {
            using var conn = new SQLiteConnection($"Data Source={_dbPath};");
            conn.Open();
            using var cmd = conn.CreateCommand();

            // Удаляем старые данные для этого помещения
            cmd.CommandText = "DELETE FROM asset_cache WHERE room_id = @roomId";
            cmd.Parameters.AddWithValue("@roomId", roomId);
            cmd.ExecuteNonQuery();

            // Загружаем новые
            foreach (var asset in assets)
            {
                cmd.CommandText = @"
                    INSERT OR REPLACE INTO asset_cache 
                    (rfid_tag, asset_name, inventory_number, room_id, last_updated, is_active)
                    VALUES (@tag, @name, @inv, @roomId, @time, 1)";
                cmd.Parameters.Clear();
                cmd.Parameters.AddWithValue("@tag", asset.RfidTag);
                cmd.Parameters.AddWithValue("@name", asset.Name ?? "");
                cmd.Parameters.AddWithValue("@inv", asset.InventoryNumber ?? "");
                cmd.Parameters.AddWithValue("@roomId", roomId);
                cmd.Parameters.AddWithValue("@time", DateTime.Now.ToString("o"));
                cmd.ExecuteNonQuery();
            }

            return true;
        }
    }

    /// <summary>
    /// Проверить актив по локальному кэшу (мгновенно, без сети)
    /// </summary>
    public (bool Found, string AssetName, string InventoryNumber) CheckLocalCache(string rfidTag)
    {
        lock (_lock)
        {
            using var conn = new SQLiteConnection($"Data Source={_dbPath};");
            conn.Open();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT asset_name, inventory_number FROM asset_cache WHERE rfid_tag = @tag AND is_active = 1";
            cmd.Parameters.AddWithValue("@tag", rfidTag);
            
            using var reader = cmd.ExecuteReader();
            if (reader.Read())
            {
                return (
                    Found: true,
                    AssetName: reader["asset_name"].ToString() ?? "",
                    InventoryNumber: reader["inventory_number"].ToString() ?? ""
                );
            }
            return (Found: false, "", "");
        }
    }

    /// <summary>
    /// Получить список ожидаемых тегов для помещения
    /// </summary>
    public List<string> GetExpectedTags(int roomId)
    {
        lock (_lock)
        {
            using var conn = new SQLiteConnection($"Data Source={_dbPath};");
            conn.Open();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT rfid_tag FROM asset_cache WHERE room_id = @roomId AND is_active = 1";
            cmd.Parameters.AddWithValue("@roomId", roomId);
            
            var tags = new List<string>();
            using var reader = cmd.ExecuteReader();
            while (reader.Read())
                tags.Add(reader["rfid_tag"].ToString()!);
            
            return tags;
        }
    }

    /// <summary>
    /// Пометить актив как пропущенный (спрятан, отложен)
    /// </summary>
    public void MarkDeferred(string rfidTag, string note = "")
    {
        lock (_lock)
        {
            using var conn = new SQLiteConnection($"Data Source={_dbPath};");
            conn.Open();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "UPDATE asset_cache SET is_active = 0 WHERE rfid_tag = @tag";
            cmd.Parameters.AddWithValue("@tag", rfidTag);
            cmd.ExecuteNonQuery();
        }
    }
}
