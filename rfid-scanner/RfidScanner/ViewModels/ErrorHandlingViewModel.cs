using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using System.Runtime.CompilerServices;
using RfidScanner.Models;
using RfidScanner.Services;

namespace RfidScanner.ViewModels;

/// <summary>
/// ViewModel для обработки ошибок считывания
/// </summary>
public class ErrorHandlingViewModel : INotifyPropertyChanged
{
    private readonly SessionManager _sessionManager;
    private readonly LocalStoreService _localStore;
    private readonly SilentModeService _silentMode;
    private readonly Action<string, ScanAssetStatus, string?, string?> _onConfirm;

    private ScanErrorRecord? _selectedError;
    private string _hintText = "";
    private bool _hasErrors;

    public ObservableCollection<ScanErrorRecord> UnresolvedErrors { get; } = new();

    public ErrorHandlingViewModel(SessionManager sessionManager, LocalStoreService localStore, 
        SilentModeService silentMode, Action<string, ScanAssetStatus, string?, string?> onConfirm)
    {
        _sessionManager = sessionManager;
        _localStore = localStore;
        _silentMode = silentMode;
        _onConfirm = onConfirm;
    }

    public ScanErrorRecord? SelectedError
    {
        get => _selectedError;
        set => SetProperty(ref _selectedError, value);
    }

    public string HintText
    {
        get => _hintText;
        private set => SetProperty(ref _hintText, value);
    }

    public bool HasErrors
    {
        get => _hasErrors;
        private set => SetProperty(ref _hasErrors, value);
    }

    /// <summary>
    /// Получить подсказку по типу ошибки
    /// </summary>
    public static (string Message, string Hint) GetErrorInfo(ScanErrorType errorType)
    {
        return errorType switch
        {
            ScanErrorType.NoRead => (
                "❌ Метка не считана",
                "Метка не считана. Попробуйте поднести сканер ближе (1-3 см) и под другим углом."
            ),
            ScanErrorType.Interference => (
                "⚠️ Помехи при считывании",
                "Возможно, метка экранирована металлом или другими объектами. Уберите препятствия и повторите."
            ),
            ScanErrorType.Duplicate => (
                "🔄 Дубликат считывания",
                "Эта метка уже была считана. Пропустите."
            ),
            ScanErrorType.WeakSignal => (
                "📶 Слабый сигнал",
                "Сигнал слишком слабый. Проверьте, что метка не повреждена и не скрыта."
            ),
            _ => ("❓ Неизвестная ошибка", "Попробуйте поднести сканер ближе к метке.")
        };
    }

    /// <summary>
    /// Обновить список нерешённых ошибок
    /// </summary>
    public void RefreshErrors()
    {
        UnresolvedErrors.Clear();
        if (_sessionManager.CurrentSession == null) return;

        var errors = _localStore.GetUnresolvedErrors(_sessionManager.CurrentSession.Id);
        foreach (var error in errors)
            UnresolvedErrors.Add(error);

        HasErrors = errors.Count > 0;

        if (HasErrors && SelectedError == null)
            SelectedError = errors[0];

        if (SelectedError != null)
        {
            var info = GetErrorInfo(SelectedError.ErrorType);
            HintText = info.Hint;
        }
    }

    /// <summary>
    /// Пропустить ошибку (отметить как решённую)
    /// </summary>
    public void SkipError()
    {
        if (SelectedError == null) return;
        ResolveError("skipped");
    }

    /// <summary>
    /// Подтвердить вручную (актив найден)
    /// </summary>
    public void ConfirmManually(string assetName, string inventoryNumber)
    {
        if (SelectedError == null) return;
        _onConfirm(SelectedError.RfidTag, ScanAssetStatus.Matched, assetName, inventoryNumber);
        ResolveError("manually_confirmed");
    }

    /// <summary>
    /// Повторить считывание
    /// </summary>
    public void RetryRead()
    {
        if (SelectedError == null) return;
        
        SelectedError.RetryCount++;
        if (SelectedError.RetryCount >= 3)
        {
            // После 3 попыток — предлагаем пропустить
            HintText = "⚠️ После 3 попыток метка всё ещё не считана. Рекомендуется пропустить.";
        }
        else
        {
            HintText = $"🔄 Попытка {SelectedError.RetryCount + 1}/3. Поднесите сканер ближе.";
        }
    }

    private void ResolveError(string resolvedBy)
    {
        if (SelectedError == null || _sessionManager.CurrentSession == null) return;
        
        _localStore.ResolveScanError(_sessionManager.CurrentSession.Id, SelectedError.RfidTag, resolvedBy);
        SelectedError.IsResolved = true;
        SelectedError.ResolvedBy = resolvedBy;
        
        RefreshErrors();
    }

    public event PropertyChangedEventHandler? PropertyChanged;
    protected void OnPropertyChanged([CallerMemberName] string? name = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
    }
    protected bool SetProperty<T>(ref T field, T value, [CallerMemberName] string? name = null)
    {
        if (Equals(field, value)) return false;
        field = value;
        OnPropertyChanged(name);
        return true;
    }
}
