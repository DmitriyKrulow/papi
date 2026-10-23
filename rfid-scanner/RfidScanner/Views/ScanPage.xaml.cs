using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media.Animation;
using RfidScanner.Models;
using RfidScanner.Services;
using RfidScanner.ViewModels;

namespace RfidScanner.Views;

/// <summary>
/// Interaction logic for ScanPage.xaml
/// </summary>
public partial class ScanPage : UserControl
{
    private readonly ScanViewModel _viewModel;
    private readonly SessionManager _sessionManager;
    private readonly AssetDetailDialog? _detailDialog;
    private Storyboard? _pulseStoryboard;

    public ScanPage(ScanViewModel viewModel, SessionManager sessionManager)
    {
        _viewModel = viewModel;
        _sessionManager = sessionManager;
        
        InitializeComponent();
        DataContext = _viewModel;
        
        // Диалог деталей
        _detailDialog = new AssetDetailDialog();
        
        // Подписка на события сессии
        _sessionManager.SessionChanged += OnSessionChanged;
        
        // Получаем ссылку на storyboard из ресурсов
        _pulseStoryboard = (Storyboard)FindResource("ScanPulseStoryboard");
        
        // Подписка на обновление результатов (пульсация при сканировании)
        _viewModel.PropertyChanged += (s, e) =>
        {
            if (e.PropertyName == nameof(ScanViewModel.MatchedCount) && _viewModel.MatchedCount > 0)
            {
                TriggerScanPulse();
            }
        };
    }

    /// <summary>
    /// Запускает анимацию пульсации при успешном сканировании
    /// </summary>
    private void TriggerScanPulse()
    {
        if (_pulseStoryboard == null || ScanPulseBorder == null)
            return;

        // Копируем storyboard чтобы можно было запускать повторно
        var clone = (Storyboard)_pulseStoryboard.Clone();
        clone.Begin(ScanPulseBorder);
    }

    private void OnSessionChanged(ScanSession session)
    {
        // ViewModel обновляется через события
    }

    private void PauseButton_Click(object sender, RoutedEventArgs e)
    {
        _sessionManager.PauseSession();
        PauseBtn.Visibility = Visibility.Collapsed;
        ResumeBtn.Visibility = Visibility.Visible;
    }

    private void ResumeButton_Click(object sender, RoutedEventArgs e)
    {
        _sessionManager.ResumeSession();
        PauseBtn.Visibility = Visibility.Visible;
        ResumeBtn.Visibility = Visibility.Collapsed;
    }

    private void SkipButton_Click(object sender, RoutedEventArgs e)
    {
        _viewModel.SkipCommand.Execute(null);
    }

    private void FinishButton_Click(object sender, RoutedEventArgs e)
    {
        if (MessageBox.Show("Завершить инвентаризацию? Результаты будут отправлены на сервер.",
            "Подтверждение", MessageBoxButton.YesNo, MessageBoxImage.Question) == MessageBoxResult.Yes)
        {
            _sessionManager.FinishSession();
            _viewModel.SyncCommand.Execute(null);
        }
    }

    private void ResultListView_MouseDoubleClick(object sender, MouseButtonEventArgs e)
    {
        var listView = sender as ListView;
        if (listView?.SelectedItem is ScanResultItem selected)
        {
            ShowAssetDetails(selected);
        }
    }

    private void ShowAssetDetails(ScanResultItem item)
    {
        if (_detailDialog == null) return;
        
        _detailDialog.SetData(
            rfidTag: item.RfidTag,
            assetName: item.AssetName ?? "Неизвестный актив",
            inventoryNumber: item.InventoryNumber ?? "—",
            status: item.Status,
            note: item.Note,
            scannedAt: item.ScannedAt
        );
        
        _detailDialog.ShowDialog();
    }
}
