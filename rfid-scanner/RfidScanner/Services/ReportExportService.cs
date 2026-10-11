using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using RfidScanner.Models;

namespace RfidScanner.Services;

/// <summary>
/// Сервис экспорта отчётов в CSV/JSON
/// </summary>
public class ReportExportService
{
    /// <summary>
    /// Экспорт результатов сканирования в CSV (открывается в Excel)
    /// </summary>
    public string ExportToCsv(List<ScanResultItem> results, ReportParameters parameters, string currentUser)
    {
        var sb = new StringBuilder();
        
        // Заголовок
        sb.AppendLine("Отчёт по инвентаризации");
        sb.AppendLine($"Помещение: {parameters.RoomName}");
        sb.AppendLine($"Период: {parameters.FromDate:dd.MM.yyyy} — {parameters.ToDate:dd.MM.yyyy}");
        sb.AppendLine($"Пользователь: {currentUser}");
        sb.AppendLine($"Дата формирования: {DateTime.Now:dd.MM.yyyy HH:mm:ss}");
        sb.AppendLine();
        
        // Разделитель
        sb.AppendLine("RFID-метка;Инвентарный номер;Название актива;Тип;Статус;Ответственный;Время проверки;Примечание");
        
        // Данные
        foreach (var item in results)
        {
            sb.AppendLine($"{item.RfidTag};" +
                         $"{item.InventoryNumber ?? "—"};" +
                         $"{item.AssetName ?? "—"};" +
                         $"{GetStatusText(item.Status)};" +
                         $"{item.ScannedAt:dd.MM.yyyy HH:mm};" +
                         $"{item.Note ?? "—"}");
        }
        
        // Итого
        sb.AppendLine();
        sb.AppendLine($"Итого: {results.Count} активов");
        sb.AppendLine($"Найдено: {results.Count(r => r.Status == ScanAssetStatus.Matched)}");
        sb.AppendLine($"Лишние: {results.Count(r => r.Status == ScanAssetStatus.Extra)}");
        sb.AppendLine($"Пропущены: {results.Count(r => r.Status == ScanAssetStatus.Missing)}");
        
        return sb.ToString();
    }

    /// <summary>
    /// Экспорт в JSON
    /// </summary>
    public string ExportToJson(List<ScanResultItem> results, ReportParameters parameters, string currentUser)
    {
        var data = new
        {
            report_title = "Отчёт по инвентаризации PAPI",
            room_name = parameters.RoomName,
            period_from = parameters.FromDate.ToString("o"),
            period_to = parameters.ToDate.ToString("o"),
            generated_by = currentUser,
            generated_at = DateTime.Now.ToString("o"),
            summary = new
            {
                total = results.Count,
                matched = results.Count(r => r.Status == ScanAssetStatus.Matched),
                extra = results.Count(r => r.Status == ScanAssetStatus.Extra),
                missing = results.Count(r => r.Status == ScanAssetStatus.Missing)
            },
            items = results.Select(r => new
            {
                rfid_tag = r.RfidTag,
                inventory_number = r.InventoryNumber,
                asset_name = r.AssetName,
                status = r.Status.ToString(),
                scanned_at = r.ScannedAt.ToString("o"),
                note = r.Note
            }).ToList()
        };

        return Newtonsoft.Json.JsonConvert.SerializeObject(data, Newtonsoft.Json.Formatting.Indented);
    }

    /// <summary>
    /// Сохранить файл и открыть диалог сохранения
    /// </summary>
    public (bool Success, string FilePath)? SaveFileDialog(
        List<ScanResultItem> results, ReportParameters parameters, string currentUser, ReportFormat format)
    {
        var dialog = new Microsoft.Win32.SaveFileDialog
        {
            Filter = format switch
            {
                ReportFormat.Csv => "CSV-файл (*.csv)|*.csv|Все файлы (*.*)|*.*",
                ReportFormat.Json => "JSON-файл (*.json)|*.json|Все файлы (*.*)|*.*",
                _ => "CSV-файл (*.csv)|*.csv"
            },
            DefaultExt = format == ReportFormat.Csv ? ".csv" : ".json",
            FileName = $"InventoryReport_{parameters.RoomName}_{DateTime.Now:yyyyMMdd_HHmmss}"
        };

        if (dialog.ShowDialog() != true) return null;

        string content;
        if (format == ReportFormat.Csv)
            content = ExportToCsv(results, parameters, currentUser);
        else
            content = ExportToJson(results, parameters, currentUser);

        File.WriteAllText(dialog.FileName, content, Encoding.UTF8);
        return (Success: true, FilePath: dialog.FileName);
    }

    private string GetStatusText(ScanAssetStatus status)
    {
        return status switch
        {
            ScanAssetStatus.Matched => "Совпадает",
            ScanAssetStatus.Extra => "Лишний",
            ScanAssetStatus.Missing => "Не найден",
            ScanAssetStatus.Error => "Ошибка",
            _ => "Неизвестно"
        };
    }
}
