using System.Windows;
using System.Windows.Controls;
using RfidScanner.Models;
using RfidScanner.ViewModels;

namespace RfidScanner.Views;

/// <summary>
/// Interaction logic for ScanView.xaml
/// </summary>
public partial class ScanView : UserControl
{
    private ScanViewModel? _viewModel;

    public ScanView()
    {
        InitializeComponent();
        // Подписываемся на загруженность для инициализации
        Loaded += ScanView_Loaded;
    }
    
    private void ScanView_Loaded(object sender, RoutedEventArgs e)
    {
        // Инициализация теперь происходит в Initialize(), этот метод больше не нужен
        // Оставляем для совместимости
    }

    public void Initialize(ScanViewModel viewModel)
    {
        _viewModel = viewModel;
        DataContext = viewModel;
        
        // Подписываемся на событие обновления результатов
        _viewModel.ResultsUpdated += UpdateResultsList;
        
        // Подписываемся на событие завершения инвентаризации
        _viewModel.InventoryCompleted += () =>
        {
            InventoryCompleted?.Invoke();
        };
        
        // Подписываемся на события изменения свойств для обновления UI
        _viewModel.PropertyChanged += (s, e) =>
        {
            if (e.PropertyName == nameof(ScanViewModel.MatchedCount))
                MatchedCountText.Text = _viewModel.MatchedCount.ToString();
            else if (e.PropertyName == nameof(ScanViewModel.ExtraCount))
                ExtraCountText.Text = _viewModel.ExtraCount.ToString();
            else if (e.PropertyName == nameof(ScanViewModel.MissingCount))
                MissingCountText.Text = _viewModel.MissingCount.ToString();
            else if (e.PropertyName == nameof(ScanViewModel.TotalCount))
                TotalCountText.Text = _viewModel.TotalCount.ToString();
            else if (e.PropertyName == nameof(ScanViewModel.ConfirmedCount))
                // Обновляем прогресс при изменении подтверждённых
                UpdateProgress();
            else if (e.PropertyName == nameof(ScanViewModel.SessionRoomName))
                RoomNameText.Text = $"🏢 Помещение: {_viewModel.SessionRoomName}";
            else if (e.PropertyName == nameof(ScanViewModel.StatusText))
                StatusText.Text = _viewModel.StatusText;
            else if (e.PropertyName == nameof(ScanViewModel.LastTag))
                LastTagText.Text = string.IsNullOrEmpty(_viewModel.LastTag) ? "—" : _viewModel.LastTag;
            else if (e.PropertyName == nameof(ScanViewModel.HasResults))
                UpdateResultsList();
            else if (e.PropertyName is nameof(ScanViewModel.ConfirmedCount) or nameof(ScanViewModel.TotalCount))
                UpdateProgress();
        };
        
        // Обновляем имя помещения
        RoomNameText.Text = $"🏢 Помещение: {_viewModel!.SessionRoomName}";
        
        // ВРУЧНУЮ обновляем UI текущими значениями (потому что TotalCount мог установиться ДО подписки)
        MatchedCountText.Text = _viewModel.MatchedCount.ToString();
        ExtraCountText.Text = _viewModel.ExtraCount.ToString();
        MissingCountText.Text = _viewModel.MissingCount.ToString();
        TotalCountText.Text = _viewModel.TotalCount.ToString();
        StatusText.Text = _viewModel.StatusText;
        LastTagText.Text = string.IsNullOrEmpty(_viewModel.LastTag) ? "—" : _viewModel.LastTag;
        
        // Привязываем список активов помещения
        RoomAssetsList.ItemsSource = _viewModel.RoomAssets;
        TotalAssetsText.Text = _viewModel.RoomAssets.Count.ToString();
        EmptyAssetsText.Visibility = _viewModel.RoomAssets.Count > 0 ? Visibility.Collapsed : Visibility.Visible;
        
        // Подписываемся на изменение количества активов (ObservableCollection не вызывает PropertyChanged при добавлении)
        _viewModel.RoomAssets.CollectionChanged += (s, e) =>
        {
            TotalAssetsText.Text = _viewModel.RoomAssets.Count.ToString();
            EmptyAssetsText.Visibility = _viewModel.RoomAssets.Count > 0 ? Visibility.Collapsed : Visibility.Visible;
        };
        
        // Обновляем прогресс
        UpdateProgress();
        
        System.Diagnostics.Debug.WriteLine($"[ScanView.Initialize] UI updated: TotalCount={_viewModel.TotalCount}, RoomAssets={_viewModel.RoomAssets.Count}, Matched={_viewModel.MatchedCount}");
    }
    
    private void UpdateProgress()
    {
        if (_viewModel != null)
        {
            ProgressText.Text = $"{_viewModel.ConfirmedCount} / {_viewModel.TotalCount}";
            ProgressPercentText.Text = $"{_viewModel.ProgressPercent}%";
            // Обновляем ProgressBar вручную (так как ProgressPercent — вычисляемое свойство)
            if (ProgressPercentBar != null)
            {
                ProgressPercentBar.Value = _viewModel.ProgressPercent;
            }
        }
    }
    
    private void UpdateResultsList()
    {
        System.Diagnostics.Debug.WriteLine($"[UpdateResultsList] Called, viewModel={_viewModel != null}, AllResults={_viewModel?.AllResults.Count ?? 0}");
        if (_viewModel == null) return;
        
        ResultsList.Items.Clear();
        
        // Добавляем последние 50 результатов
        var results = _viewModel.AllResults.ToList();
        System.Diagnostics.Debug.WriteLine($"[UpdateResultsList] Adding {results.Count} results to ListView");
        var start = Math.Max(0, results.Count - 50);
        for (int i = start; i < results.Count; i++)
        {
            ResultsList.Items.Add(results[i]);
        }
        System.Diagnostics.Debug.WriteLine($"[UpdateResultsList] ListView Items count: {ResultsList.Items.Count}");
        
        // Автопрокрутка к последнему результату
        if (ResultsList.Items.Count > 0)
        {
            ResultsList.ScrollIntoView(ResultsList.Items[ResultsList.Items.Count - 1]);
        }
    }

    private void PauseButton_Click(object sender, RoutedEventArgs e)
    {
        if (_viewModel == null) return;
        
        _viewModel.TogglePause();
        
        if (_viewModel.IsPaused)
        {
            PauseButton.Content = "▶ Продолжить";
            StatusText.Text = "⏸ Сканирование приостановлено";
        }
        else
        {
            PauseButton.Content = "⏸ Пауза";
            StatusText.Text = "🔄 Сканирование продолжено";
        }
    }

    private void SkipUncheckedButton_Click(object sender, RoutedEventArgs e)
    {
        if (_viewModel == null) return;
        
        var uncheckedCount = _viewModel.RoomAssets.Count(i => !i.IsChecked);
        
        if (uncheckedCount == 0)
        {
            StatusText.Text = "✅ Все активы проверены";
            return;
        }
        
        if (MessageBox.Show(
            $"Пропустить {uncheckedCount} непроверенных активов?\n\n" +
            $"Они будут помечены как отсутствующие в инвентаризации.\n\n" +
            $"Найдено: {_viewModel.MatchedCount}\n" +
            $"Пропущено: {_viewModel.MissingCount}\n" +
            $"Осталось проверить: {uncheckedCount}",
            "Пропуск непроверенных",
            MessageBoxButton.YesNo,
            MessageBoxImage.Question) == MessageBoxResult.No)
        {
            return;
        }
        
        _ = _viewModel.SkipAllUnchecked();
    }

    private void ContinueButton_Click(object sender, RoutedEventArgs e)
    {
        // Для будущего использования
        StatusText.Text = "▶ Сканирование продолжено";
    }

    private void FinishButton_Click(object sender, RoutedEventArgs e)
    {
        System.Diagnostics.Debug.WriteLine("[ScanView] FinishButton_Click called");
        Finished?.Invoke();
        System.Diagnostics.Debug.WriteLine("[ScanView] Finished event fired");
    }

    private void ResetButton_Click(object sender, RoutedEventArgs e)
    {
        Reset?.Invoke();
    }

    private void ExitButton_Click(object sender, RoutedEventArgs e)
    {
        // Выход из режима сканирования без завершения сессии
        Exit?.Invoke();
    }

    private void ConfirmAllButton_Click(object sender, RoutedEventArgs e)
    {
        if (_viewModel == null) return;
        
        // Подтверждаем все найденные активы
        _viewModel.ConfirmAllFoundCommand.Execute(null);
    }

    private void ConfirmAssetButton_Click(object sender, RoutedEventArgs e)
    {
        if (_viewModel == null) return;
        
        var button = sender as Button;
        if (button?.DataContext is AssetDisplayItem item)
        {
            // Подтверждаем конкретный актив через команду
            _viewModel.ConfirmAssetCommand.Execute(item.AssetName);
        }
    }

    public event Action? Finished;
    public event Action? Reset;
    public event Action? Exit;
    public event Action? InventoryCompleted;
}
