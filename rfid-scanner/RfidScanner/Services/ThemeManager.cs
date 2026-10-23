using System;
using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Effects;

namespace RfidScanner.Services;

public enum AppTheme { Light, Dark }

public static class ThemeManager
{
    public static AppTheme Current { get; private set; } = AppTheme.Light;

    private static ResourceDictionary? _lightDict;
    private static ResourceDictionary? _darkDict;
    private static ConfigService? _configService;

    public static void SetConfigService(ConfigService config)
    {
        _configService = config;
    }

    public static void Apply(AppTheme theme, Application app)
    {
        try
        {
            Current = theme;

            if (_lightDict == null)
                _lightDict = CreateLightTheme();
            if (_darkDict == null)
                _darkDict = CreateDarkTheme();

            if (app.Resources.MergedDictionaries.Count > 0)
                app.Resources.MergedDictionaries.RemoveAt(0);

            app.Resources.MergedDictionaries.Add(theme == AppTheme.Light ? _lightDict : _darkDict);
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[ThemeManager] ERROR: {ex.Message}");
        }
    }

    private static ResourceDictionary CreateLightTheme()
    {
        var dict = new ResourceDictionary();
        
        // Основные цвета
        dict["ThemeBg"] = new SolidColorBrush(Color.FromRgb(0xF5, 0xF5, 0xF5));
        dict["ThemeCardBg"] = new SolidColorBrush(Color.FromRgb(0xFF, 0xFF, 0xFF));
        dict["ThemeTextPrimary"] = new SolidColorBrush(Color.FromRgb(0x21, 0x21, 0x21));
        dict["ThemeTextSecondary"] = new SolidColorBrush(Color.FromRgb(0x75, 0x75, 0x75));
        dict["ThemeAccent"] = new SolidColorBrush(Color.FromRgb(0x4F, 0x6A, 0x8C));
        dict["ThemeAccentBright"] = new SolidColorBrush(Color.FromRgb(0x2D, 0xD4, 0xEB));
        dict["ThemeSuccess"] = new SolidColorBrush(Color.FromRgb(0x4C, 0xAF, 0x50));
        dict["ThemeWarning"] = new SolidColorBrush(Color.FromRgb(0xFF, 0x98, 0x00));
        dict["ThemeError"] = new SolidColorBrush(Color.FromRgb(0xF4, 0x43, 0x36));
        dict["ThemeInfo"] = new SolidColorBrush(Color.FromRgb(0x21, 0x96, 0xF3));
        dict["ThemeBorderBrush"] = new SolidColorBrush(Color.FromRgb(0xE0, 0xE0, 0xE0));
        dict["ThemeCardBorder"] = new SolidColorBrush(Color.FromRgb(0xE8, 0xE8, 0xE8));
        
        // Фоны
        dict["ThemeHeaderBg"] = new SolidColorBrush(Color.FromRgb(0x2C, 0x32, 0x3A));
        dict["ThemeSidebarBg"] = new SolidColorBrush(Color.FromRgb(0x1E, 0x22, 0x26));
        dict["ThemeSidebarActiveBg"] = new SolidColorBrush(Color.FromRgb(0x3A, 0x40, 0x48));
        dict["ThemeSidebarHoverBg"] = new SolidColorBrush(Color.FromRgb(0x2E, 0x33, 0x3B));
        dict["ThemeTextOnDark"] = new SolidColorBrush(Color.FromRgb(0xE5, 0xE7, 0xEB));
        dict["ThemeSurfaceBg"] = new SolidColorBrush(Color.FromRgb(0xFA, 0xFA, 0xFA));
        dict["ThemeInputBg"] = new SolidColorBrush(Color.FromRgb(0xFF, 0xFF, 0xFF));
        dict["ThemeInputBorder"] = new SolidColorBrush(Color.FromRgb(0xDE, 0xDE, 0xDE));
        dict["ThemeProgressBarBg"] = new SolidColorBrush(Color.FromRgb(0xE0, 0xE0, 0xE0));
        
        // Виджеты
        dict["ThemeWidgetSuccessBg"] = new SolidColorBrush(Color.FromRgb(0xE8, 0xF5, 0xE9));
        dict["ThemeWidgetWarningBg"] = new SolidColorBrush(Color.FromRgb(0xFF, 0xF8, 0xE1));
        dict["ThemeWidgetErrorBg"] = new SolidColorBrush(Color.FromRgb(0xFF, 0xEB, 0xEE));
        dict["ThemeWidgetInfoBg"] = new SolidColorBrush(Color.FromRgb(0xE3, 0xF2, 0xFD));
        
        // ListView / ListBox
        dict["ThemeListBoxBg"] = new SolidColorBrush(Color.FromRgb(0xFF, 0xFF, 0xFF));
        dict["ThemeListViewBg"] = new SolidColorBrush(Color.FromRgb(0xFF, 0xFF, 0xFF));
        dict["ThemeListBoxItemBg"] = new SolidColorBrush(Color.FromRgb(0xFF, 0xFF, 0xFF));
        dict["ThemeListBoxItemHoverBg"] = new SolidColorBrush(Color.FromRgb(0xF5, 0xF5, 0xF5));
        dict["ThemeListBoxItemSelectedBg"] = new SolidColorBrush(Color.FromRgb(0xE3, 0xF2, 0xFD));
        
        // ScrollViewer / ScrollBar
        dict["ThemeScrollViewerBg"] = new SolidColorBrush(Color.FromRgb(0xFF, 0xFF, 0xFF));
        dict["ThemeScrollBarBg"] = new SolidColorBrush(Color.FromRgb(0xF0, 0xF0, 0xF0));
        dict["ThemeScrollBarThumbBg"] = new SolidColorBrush(Color.FromRgb(0xC0, 0xC0, 0xC0));
        dict["ThemeScrollBarThumbHoverBg"] = new SolidColorBrush(Color.FromRgb(0xA0, 0xA0, 0xA0));
        
        // TextBox / Input
        dict["ThemeTextBoxBg"] = new SolidColorBrush(Color.FromRgb(0xFF, 0xFF, 0xFF));
        dict["ThemeTextBoxForeground"] = new SolidColorBrush(Color.FromRgb(0x21, 0x21, 0x21));
        dict["ThemeTextBoxBorder"] = new SolidColorBrush(Color.FromRgb(0xDE, 0xDE, 0xDE));
        
        // TabControl / TabItem
        dict["ThemeTabControlBg"] = new SolidColorBrush(Color.FromRgb(0xFA, 0xFA, 0xFA));
        dict["ThemeTabItemBg"] = new SolidColorBrush(Color.FromRgb(0xF5, 0xF5, 0xF5));
        dict["ThemeTabItemForeground"] = new SolidColorBrush(Color.FromRgb(0x75, 0x75, 0x75));
        dict["ThemeTabItemSelectedBg"] = new SolidColorBrush(Color.FromRgb(0xE3, 0xF2, 0xFD));
        dict["ThemeTabItemSelectedForeground"] = new SolidColorBrush(Color.FromRgb(0x4F, 0x6A, 0x8C));
        
        // Button
        dict["ThemeButtonBg"] = new SolidColorBrush(Color.FromRgb(0xF5, 0xF5, 0xF5));
        dict["ThemeButtonForeground"] = new SolidColorBrush(Color.FromRgb(0x21, 0x21, 0x21));
        dict["ThemeButtonBorder"] = new SolidColorBrush(Color.FromRgb(0xE0, 0xE0, 0xE0));
        dict["ThemeButtonHoverBg"] = new SolidColorBrush(Color.FromRgb(0xEE, 0xEE, 0xEE));
        
        // Window / Chrome
        dict["ThemeWindowBg"] = new SolidColorBrush(Color.FromRgb(0xF5, 0xF5, 0xF5));
        dict["ThemeWindowTitleBg"] = new SolidColorBrush(Color.FromRgb(0x2C, 0x32, 0x3A));
        dict["ThemeWindowTitleForeground"] = new SolidColorBrush(Color.FromRgb(0xE5, 0xE7, 0xEB));
        
        return dict;
    }

    private static ResourceDictionary CreateDarkTheme()
    {
        var dict = new ResourceDictionary();
        
        // Основные цвета
        dict["ThemeBg"] = new SolidColorBrush(Color.FromRgb(0x0D, 0x0E, 0x10));
        dict["ThemeCardBg"] = new SolidColorBrush(Color.FromRgb(0x1A, 0x1C, 0x20));
        dict["ThemeTextPrimary"] = new SolidColorBrush(Color.FromRgb(0xF0, 0xF2, 0xF4));
        dict["ThemeTextSecondary"] = new SolidColorBrush(Color.FromRgb(0x9E, 0xA2, 0xA8));
        dict["ThemeAccent"] = new SolidColorBrush(Color.FromRgb(0x4F, 0x6A, 0x8C));
        dict["ThemeAccentBright"] = new SolidColorBrush(Color.FromRgb(0x2D, 0xD4, 0xEB));
        dict["ThemeSuccess"] = new SolidColorBrush(Color.FromRgb(0x34, 0xD0, 0x8C));
        dict["ThemeWarning"] = new SolidColorBrush(Color.FromRgb(0xF5, 0xA6, 0x23));
        dict["ThemeError"] = new SolidColorBrush(Color.FromRgb(0xEF, 0x53, 0x50));
        dict["ThemeInfo"] = new SolidColorBrush(Color.FromRgb(0x42, 0xA5, 0xF5));
        dict["ThemeBorderBrush"] = new SolidColorBrush(Color.FromRgb(0x2A, 0x2D, 0x32));
        dict["ThemeCardBorder"] = new SolidColorBrush(Color.FromRgb(0x2A, 0x2D, 0x32));
        
        // Фоны
        dict["ThemeHeaderBg"] = new SolidColorBrush(Color.FromRgb(0x14, 0x15, 0x18));
        dict["ThemeSidebarBg"] = new SolidColorBrush(Color.FromRgb(0x0A, 0x0B, 0x0C));
        dict["ThemeSidebarActiveBg"] = new SolidColorBrush(Color.FromRgb(0x22, 0x24, 0x28));
        dict["ThemeSidebarHoverBg"] = new SolidColorBrush(Color.FromRgb(0x1C, 0x1E, 0x22));
        dict["ThemeTextOnDark"] = new SolidColorBrush(Color.FromRgb(0xF0, 0xF2, 0xF4));
        dict["ThemeSurfaceBg"] = new SolidColorBrush(Color.FromRgb(0x14, 0x15, 0x18));
        dict["ThemeInputBg"] = new SolidColorBrush(Color.FromRgb(0x1A, 0x1C, 0x20));
        dict["ThemeInputBorder"] = new SolidColorBrush(Color.FromRgb(0x2A, 0x2D, 0x32));
        dict["ThemeProgressBarBg"] = new SolidColorBrush(Color.FromRgb(0x2A, 0x2D, 0x32));
        
        // Виджеты
        dict["ThemeWidgetSuccessBg"] = new SolidColorBrush(Color.FromRgb(0x1B, 0x5E, 0x20));
        dict["ThemeWidgetWarningBg"] = new SolidColorBrush(Color.FromRgb(0x4A, 0x3B, 0x00));
        dict["ThemeWidgetErrorBg"] = new SolidColorBrush(Color.FromRgb(0x60, 0x14, 0x11));
        dict["ThemeWidgetInfoBg"] = new SolidColorBrush(Color.FromRgb(0x0D, 0x47, 0xA1));
        
        // ListView / ListBox
        dict["ThemeListBoxBg"] = new SolidColorBrush(Color.FromRgb(0x1A, 0x1C, 0x20));
        dict["ThemeListViewBg"] = new SolidColorBrush(Color.FromRgb(0x1A, 0x1C, 0x20));
        dict["ThemeListBoxItemBg"] = new SolidColorBrush(Color.FromRgb(0x1A, 0x1C, 0x20));
        dict["ThemeListBoxItemHoverBg"] = new SolidColorBrush(Color.FromRgb(0x22, 0x24, 0x28));
        dict["ThemeListBoxItemSelectedBg"] = new SolidColorBrush(Color.FromRgb(0x0D, 0x47, 0xA1));
        
        // ScrollViewer / ScrollBar
        dict["ThemeScrollViewerBg"] = new SolidColorBrush(Color.FromRgb(0x1A, 0x1C, 0x20));
        dict["ThemeScrollBarBg"] = new SolidColorBrush(Color.FromRgb(0x1A, 0x1C, 0x20));
        dict["ThemeScrollBarThumbBg"] = new SolidColorBrush(Color.FromRgb(0x2A, 0x2D, 0x32));
        dict["ThemeScrollBarThumbHoverBg"] = new SolidColorBrush(Color.FromRgb(0x3A, 0x3D, 0x42));
        
        // TextBox / Input
        dict["ThemeTextBoxBg"] = new SolidColorBrush(Color.FromRgb(0x1A, 0x1C, 0x20));
        dict["ThemeTextBoxForeground"] = new SolidColorBrush(Color.FromRgb(0xF0, 0xF2, 0xF4));
        dict["ThemeTextBoxBorder"] = new SolidColorBrush(Color.FromRgb(0x2A, 0x2D, 0x32));
        
        // TabControl / TabItem
        dict["ThemeTabControlBg"] = new SolidColorBrush(Color.FromRgb(0x14, 0x15, 0x18));
        dict["ThemeTabItemBg"] = new SolidColorBrush(Color.FromRgb(0x1A, 0x1C, 0x20));
        dict["ThemeTabItemForeground"] = new SolidColorBrush(Color.FromRgb(0x9E, 0xA2, 0xA8));
        dict["ThemeTabItemSelectedBg"] = new SolidColorBrush(Color.FromRgb(0x0D, 0x47, 0xA1));
        dict["ThemeTabItemSelectedForeground"] = new SolidColorBrush(Color.FromRgb(0x2D, 0xD4, 0xEB));
        
        // Button
        dict["ThemeButtonBg"] = new SolidColorBrush(Color.FromRgb(0x1A, 0x1C, 0x20));
        dict["ThemeButtonForeground"] = new SolidColorBrush(Color.FromRgb(0xF0, 0xF2, 0xF4));
        dict["ThemeButtonBorder"] = new SolidColorBrush(Color.FromRgb(0x2A, 0x2D, 0x32));
        dict["ThemeButtonHoverBg"] = new SolidColorBrush(Color.FromRgb(0x22, 0x24, 0x28));
        
        // Window / Chrome
        dict["ThemeWindowBg"] = new SolidColorBrush(Color.FromRgb(0x0D, 0x0E, 0x10));
        dict["ThemeWindowTitleBg"] = new SolidColorBrush(Color.FromRgb(0x14, 0x15, 0x18));
        dict["ThemeWindowTitleForeground"] = new SolidColorBrush(Color.FromRgb(0xF0, 0xF2, 0xF4));
        
        return dict;
    }

    public static void Toggle(Application app)
    {
        var newTheme = Current == AppTheme.Light ? AppTheme.Dark : AppTheme.Light;
        Apply(newTheme, app);
        
        // Сохраняем тему
        _configService?.SetTheme(newTheme == AppTheme.Light ? "Light" : "Dark");
    }

    public static DropShadowEffect CreateShadowEffect(Color? shadowColor = null, double opacity = 0.12, double blur = 12)
    {
        var color = shadowColor ?? Colors.Black;
        return new DropShadowEffect { Color = color, BlurRadius = blur, ShadowDepth = 2, Opacity = opacity, Direction = 160 };
    }
}
