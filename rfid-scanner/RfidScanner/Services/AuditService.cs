using System;
using RfidScanner.Models;

namespace RfidScanner.Services;

/// <summary>
/// Сервис аудита - логирование всех действий
/// </summary>
public class AuditService
{
    private readonly LocalStoreService _store;
    private string _currentUser = "Пользователь";

    public AuditService(LocalStoreService store)
    {
        _store = store;
    }

    public void SetCurrentUser(string username)
    {
        _currentUser = username;
    }

    public void Log(AuditAction action, string? sessionId = null, string? roomName = null, string? details = null)
    {
        var record = new AuditRecord
        {
            Action = action,
            Username = _currentUser,
            SessionId = sessionId,
            RoomName = roomName,
            Details = details
        };
        
        _store.LogAudit(record);
    }
}
