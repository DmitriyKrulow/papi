using System;
using System.Windows;
using System.Windows.Data;
using System.Windows.Media;

namespace RfidScanner.Converters;

/// <summary>
/// Конвертер bool -> Brush (true=зеленый фон, false=красный)
/// </summary>
public class BooleanToBrushConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, System.Globalization.CultureInfo culture)
    {
        if (value is bool success)
        {
            return success ? new SolidColorBrush(Color.FromRgb(232, 245, 233)) : new SolidColorBrush(Color.FromRgb(255, 235, 238));
        }
        return new SolidColorBrush(Colors.White);
    }

    public object ConvertBack(object value, Type targetType, object parameter, System.Globalization.CultureInfo culture)
    {
        throw new NotImplementedException();
    }
}
