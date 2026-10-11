using System;
using System.Globalization;
using System.Windows.Data;
using System.Windows.Media;
using RfidScanner.Models;

namespace RfidScanner.Converters;

/// <summary>
/// Конвертер статуса в цвет (Brush)
/// </summary>
public class StatusToBrushConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (value is ScanAssetStatus status)
        {
            return status switch
            {
                ScanAssetStatus.Matched => new SolidColorBrush(Color.FromRgb(76, 175, 80)),    // Зелёный
                ScanAssetStatus.Extra => new SolidColorBrush(Color.FromRgb(255, 152, 0)),      // Оранжевый
                ScanAssetStatus.Missing => new SolidColorBrush(Color.FromRgb(244, 67, 54)),    // Красный
                ScanAssetStatus.Error => new SolidColorBrush(Color.FromRgb(158, 158, 158)),    // Серый
                _ => new SolidColorBrush(Color.FromRgb(158, 158, 158))
            };
        }
        return new SolidColorBrush(Color.FromRgb(158, 158, 158));
    }

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
    {
        throw new NotImplementedException();
    }
}

/// <summary>
/// Конвертер статуса в иконку (emoji/text)
/// </summary>
public class StatusToIconConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        return value is ScanAssetStatus status ? status switch
        {
            ScanAssetStatus.Matched => "✅",
            ScanAssetStatus.Extra => "⚠️",
            ScanAssetStatus.Missing => "❌",
            ScanAssetStatus.Error => "⛔",
            _ => "❓"
        } : "❓";
    }

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
    {
        throw new NotImplementedException();
    }
}

/// <summary>
/// Конвертер статуса в текст на русском
/// </summary>
public class StatusToTextConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        return value is ScanAssetStatus status ? status switch
        {
            ScanAssetStatus.Matched => "Совпадает",
            ScanAssetStatus.Extra => "Лишний",
            ScanAssetStatus.Missing => "Не найден",
            ScanAssetStatus.Error => "Ошибка",
            _ => "Неизвестно"
        } : "Неизвестно";
    }

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
    {
        throw new NotImplementedException();
    }
}
