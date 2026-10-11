using System;
using System.Collections;
using System.Globalization;
using System.Windows;
using System.Windows.Data;

namespace RfidScanner.Converters;

/// <summary>
/// Конвертер количества элементов коллекции в Visibility
/// Count == 0 → Visible (показать сообщение "нет данных")
/// Count > 0 → Collapsed
/// </summary>
public class CollectionCountToVisibilityConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (value is ICollection collection)
        {
            return collection.Count == 0 ? Visibility.Visible : Visibility.Collapsed;
        }
        return Visibility.Collapsed;
    }

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
    {
        throw new NotImplementedException();
    }
}
