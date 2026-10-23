using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Threading;

namespace RfidScanner.Services;

public enum ToastType { Success, Warning, Error, Info }

public static class ToastService
{
    // Статический Popup для всех toast-уведомлений
    private static Popup? _popup;
    private static StackPanel? _toastContainer;
    private static readonly object _lock = new();

    private static void EnsurePopup(Window owner)
    {
        lock (_lock)
        {
            if (_popup != null && _popup.Child != null) return;

            _popup = new Popup
            {
                AllowsTransparency = true,
                PopupAnimation = PopupAnimation.Fade,
                PlacementTarget = owner,
                Placement = PlacementMode.Relative,
                HorizontalOffset = owner.Width - 320,
                VerticalOffset = 60,
                StaysOpen = true
            };

            _toastContainer = new StackPanel
            {
                HorizontalAlignment = HorizontalAlignment.Right,
                VerticalAlignment = VerticalAlignment.Top,
                Margin = new Thickness(20)
            };

            _popup.Child = _toastContainer;
        }
    }

    public static void Show(Window owner, string message, ToastType type = ToastType.Info, int durationMs = 3500)
    {
        if (owner == null) return;

        // Создаём toast-элемент
        var toastBorder = CreateToastElement(message, type);
        var timer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(durationMs) };

        // Если popup ещё не создан — создаём
        lock (_lock)
        {
            if (_popup == null || _popup.Child == null)
            {
                EnsurePopup(owner);
            }
        }

        // Показываем popup
        lock (_lock)
        {
            if (_popup != null && _toastContainer != null)
            {
                _toastContainer.Children.Add(toastBorder);

                // Анимация появления
                var fadeIn = new DoubleAnimation
                {
                    From = 0,
                    To = 1,
                    Duration = TimeSpan.FromMilliseconds(300)
                };
                fadeIn.BeginTime = TimeSpan.FromMilliseconds(100);
                toastBorder.BeginAnimation(UIElement.OpacityProperty, fadeIn);

                // Авто-скрытие
                timer.Tick += (s, e) =>
                {
                    timer.Stop();
                    RemoveToast(toastBorder);
                };
                timer.Start();
            }
        }
    }

    private static Border CreateToastElement(string message, ToastType type)
    {
        var bgColor = type == ToastType.Success ? Color.FromRgb(0x27, 0xAE, 0x60) :
                      type == ToastType.Warning ? Color.FromRgb(0xF3, 0x9C, 0x12) :
                      type == ToastType.Error ? Color.FromRgb(0xE7, 0x4C, 0x3C) :
                      Color.FromRgb(0x29, 0x80, 0xB9);

        var iconText = type == ToastType.Success ? "\u2713" :
                       type == ToastType.Warning ? "\u26A0" :
                       type == ToastType.Error ? "\u2715" : "\u2139";

        var toast = new Border
        {
            Background = new SolidColorBrush(bgColor),
            CornerRadius = new CornerRadius(8),
            Padding = new Thickness(16, 10, 16, 10),
            Margin = new Thickness(0, 0, 0, 8),
            Opacity = 0
        };

        var grid = new Grid();
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

        var icon = new TextBlock
        {
            Text = iconText,
            FontSize = 16,
            FontWeight = FontWeights.Bold,
            Foreground = new SolidColorBrush(Color.FromRgb(0xFF, 0xFF, 0xFF)),
            Margin = new Thickness(0, 0, 10, 0),
            VerticalAlignment = VerticalAlignment.Center
        };
        Grid.SetColumn(icon, 0);

        var text = new TextBlock
        {
            Text = message,
            FontSize = 13,
            Foreground = new SolidColorBrush(Color.FromRgb(0xFF, 0xFF, 0xFF)),
            VerticalAlignment = VerticalAlignment.Center,
            TextWrapping = TextWrapping.Wrap
        };
        Grid.SetColumn(text, 1);

        grid.Children.Add(icon);
        grid.Children.Add(text);
        toast.Child = grid;

        return toast;
    }

    private static void RemoveToast(Border toast)
    {
        var storyboard = new Storyboard();
        var fadeOut = new DoubleAnimation
        {
            To = 0,
            Duration = TimeSpan.FromMilliseconds(300)
        };
        Storyboard.SetTarget(fadeOut, toast);
        Storyboard.SetTargetProperty(fadeOut, new PropertyPath(UIElement.OpacityProperty));
        storyboard.Children.Add(fadeOut);
        storyboard.Completed += (s, e) =>
        {
            lock (_lock)
            {
                if (_toastContainer != null && _toastContainer.Children.Contains(toast))
                {
                    _toastContainer.Children.Remove(toast);
                }
            }
        };
        storyboard.Begin();
    }

    public static void Show(string message, ToastType type = ToastType.Info, int durationMs = 3500)
    {
        var owner = Application.Current.MainWindow;
        if (owner != null)
            Show(owner, message, type, durationMs);
    }

    public static void ShowSuccess(Window owner, string message) => Show(owner, message, ToastType.Success);
    public static void ShowWarning(Window owner, string message) => Show(owner, message, ToastType.Warning);
    public static void ShowError(Window owner, string message) => Show(owner, message, ToastType.Error);
    public static void ShowInfo(Window owner, string message) => Show(owner, message, ToastType.Info);
}
