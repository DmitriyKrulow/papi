using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Windows.Input;
using CommunityToolkit.Mvvm.Input;
using RfidScanner.Models;
using RfidScanner.Services;

namespace RfidScanner.ViewModels;

/// <summary>
/// ViewModel для истории и аудита
/// </summary>
public class AuditViewModel : INotifyPropertyChanged
{
    private readonly LocalStoreService _localStore;
    private readonly SessionManager _sessionManager;

    private ObservableCollection<AuditRecord> _history = new();
    private string _selectedUsername = "";
    private string _selectedRoom = "";

    public AuditViewModel(LocalStoreService localStore, SessionManager sessionManager)
    {
        _localStore = localStore;
        _sessionManager = sessionManager;
        LoadHistory();
    }

    public ObservableCollection<AuditRecord> History
    {
        get => _history;
        private set => SetProperty(ref _history, value);
    }

    public string SelectedUsername
    {
        get => _selectedUsername;
        set => SetProperty(ref _selectedUsername, value);
    }

    public string SelectedRoom
    {
        get => _selectedRoom;
        private set => SetProperty(ref _selectedRoom, value);
    }

    public void LoadHistory()
    {
        var records = _localStore.GetAuditHistory(100);
        History.Clear();
        foreach (var record in records)
            History.Add(record);
    }

    public ICommand RefreshCommand => new RelayCommand(Refresh);

    public void Refresh()
    {
        LoadHistory();
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
