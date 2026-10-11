using System;
using System.Globalization;
using System.Windows;
using System.Windows.Data;
using System.Windows.Media;

namespace RfidScanner.Converters;

/// <summary>
/// Инвертирует булево значение
/// </summary>
public class InverseBooleanConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (value is bool b) return !b;
        return true;
    }

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (value is bool b) return !b;
        return true;
    }
}

/// <summary>
/// Конвертер bool в Visibility
/// </summary>
public class BooleanToVisibilityConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (value is bool b)
        {
            var invert = parameter?.ToString() == "Inverse";
            return (b != invert) ? Visibility.Visible : Visibility.Collapsed;
        }
        return Visibility.Collapsed;
    }

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (value is Visibility v)
        {
            var invert = parameter?.ToString() == "Inverse";
            return (v != Visibility.Collapsed) != invert;
        }
        return false;
    }
}

/// <summary>
/// Конвертер count > 0 в фон (красный если есть расхождения)
/// </summary>
public class CountToBackgroundConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (value is int count)
        {
            return count > 0
                ? new SolidColorBrush(Color.FromRgb(255, 243, 224))  // Светло-оранжевый
                : new SolidColorBrush(Color.FromRgb(232, 245, 233)); // Светло-зелёный
        }
        return new SolidColorBrush(Colors.White);
    }

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
    {
        throw new NotImplementedException();
    }
}
