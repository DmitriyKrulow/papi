using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using RfidScanner.Models;

namespace RfidScanner.Services;

/// <summary>
/// Управляет сессиями сканирования
/// </summary>
public class SessionManager
{
    private ScanSession? _currentSession;
    private readonly LocalStoreService _store;
    private readonly AuditService _audit;

    public event Action<ScanSession>? SessionChanged;
    public event Action<string>? TagScanned;

    public ScanSession? CurrentSession => _currentSession;
    public bool HasActiveSession => _currentSession != null && _currentSession.State == SessionState.Active;
    public bool HasPausedSession => _currentSession != null && _currentSession.State == SessionState.Paused;

    public SessionManager(LocalStoreService store, AuditService audit)
    {
        _store = store;
        _audit = audit;
    }

    public void CreateSession(string roomName, int roomId, int inventoryId = 0, List<Asset>? pendingAssets = null)
    {
        _currentSession = new ScanSession
        {
            RoomName = roomName,
            RoomId = roomId,
            InventoryId = inventoryId,
            PendingAssets = pendingAssets
        };
        SessionChanged?.Invoke(_currentSession);
        _audit.Log(AuditAction.SessionStart, sessionId: _currentSession.Id, roomName: roomName, 
            details: $"Начата инвентаризация помещения {roomName} (inventory_id={inventoryId})");
        SaveAsync();
    }

    public void PauseSession()
    {
        _currentSession?.Pause();
        SessionChanged?.Invoke(_currentSession!);
        _audit.Log(AuditAction.SessionPause, sessionId: _currentSession?.Id, 
            roomName: _currentSession?.RoomName, details: "Сессия приостановлена");
        SaveAsync();
    }

    public void ResumeSession()
    {
        _currentSession?.Resume();
        SessionChanged?.Invoke(_currentSession!);
        _audit.Log(AuditAction.SessionResume, sessionId: _currentSession?.Id, 
            roomName: _currentSession?.RoomName, details: "Сессия возобновлена");
        SaveAsync();
    }

    public void FinishSession()
    {
        System.Diagnostics.Debug.WriteLine($"[SessionManager.FinishSession] BEFORE: State={_currentSession?.State}, HasActiveSession={HasActiveSession}");
        System.Diagnostics.Debug.WriteLine($"[SessionManager.FinishSession] StackTrace: {System.Environment.StackTrace}");
        _currentSession?.Finish();
        System.Diagnostics.Debug.WriteLine($"[SessionManager.FinishSession] AFTER: State={_currentSession?.State}, HasActiveSession={HasActiveSession}");
        SessionChanged?.Invoke(_currentSession!);
        _audit.Log(AuditAction.SessionFinish, sessionId: _currentSession?.Id, 
            roomName: _currentSession?.RoomName, 
            details: $"Завершена: найдено {_currentSession!.MatchedCount}, " +
                    $"лишних {_currentSession.ExtraCount}, пропущено {_currentSession.MissingCount}");
        SaveAsync();
    }

    public void ResetSession()
    {
        _currentSession?.Reset();
        SessionChanged?.Invoke(_currentSession!);
        _audit.Log(AuditAction.SessionStart, sessionId: _currentSession?.Id, 
            roomName: _currentSession?.RoomName, details: "Сессия сброшена");
    }

    public void AddTag(string rfidTag, ScanAssetStatus status, string? assetName = null, string? inventoryNumber = null)
    {
        if (_currentSession == null || _currentSession.IsPaused || _currentSession.IsFinished)
            return;

        if (_currentSession.SeenTags.Contains(rfidTag))
            return; // Дубликат

        System.Diagnostics.Debug.WriteLine($"[SessionManager.AddTag] Adding: Tag='{rfidTag}', Status={status}, Name='{assetName}'");
        
        _currentSession.SeenTags.Add(rfidTag);
        
        var result = new ScanResultItem
        {
            RfidTag = rfidTag,
            Status = status,
            AssetName = assetName,
            InventoryNumber = inventoryNumber
        };

        _currentSession.Results.Add(result);
        System.Diagnostics.Debug.WriteLine($"[SessionManager.AddTag] Results count now: {_currentSession.Results.Count}");
        
        TagScanned?.Invoke(rfidTag);
        SessionChanged?.Invoke(_currentSession);
        
        // Логирование
        var action = status switch
        {
            ScanAssetStatus.Matched => AuditAction.TagMatched,
            ScanAssetStatus.Extra => AuditAction.TagExtra,
            _ => AuditAction.TagSkipped
        };
        
        _audit.Log(action, sessionId: _currentSession.Id, 
            roomName: _currentSession.RoomName,
            details: $"{status}: {rfidTag} {(!string.IsNullOrEmpty(assetName) ? $"- {assetName}" : "")}");
        
        SaveAsync();
    }

    public void MarkManuallyConfirmed(string rfidTag, string note = "")
    {
        if (_currentSession == null) return;

        var item = _currentSession.Results.FirstOrDefault(r => r.RfidTag == rfidTag);
        if (item != null)
        {
            item.ManuallyConfirmed = true;
            item.Note = note;
            SaveAsync();
        }
    }

    private void SaveAsync()
    {
        if (_currentSession != null)
            _store.SaveSession(_currentSession);
    }

    public ScanSession? LoadSession(string sessionId)
    {
        return _store.LoadSession(sessionId);
    }
}
