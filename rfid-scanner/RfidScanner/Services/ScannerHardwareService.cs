using System;
using System.IO.Ports;
using System.Net.Sockets;
using System.Threading;
using System.Threading.Tasks;

namespace RfidScanner.Services;

/// <summary>
/// Режим тишины: звук только при расхождениях
/// </summary>
public class SilentModeService
{
    private readonly CancellationTokenSource _cts = new();

    public bool Enabled { get; set; } = true;

    /// <summary>
    /// Звук при совпадении (тихий)
    /// </summary>
    public void PlayMatch()
    {
        if (!Enabled) return;
        // Тихий короткий пик
        System.Media.SystemSounds.Asterisk.Play();
    }

    /// <summary>
    /// Звук при расхождении (громкий)
    /// </summary>
    public void PlayMismatch()
    {
        if (!Enabled) return;
        System.Media.SystemSounds.Beep.Play();
    }

    /// <summary>
    /// Звук завершения
    /// </summary>
    public void PlayComplete()
    {
        if (!Enabled) return;
        System.Media.SystemSounds.Exclamation.Play();
    }

    public void Dispose()
    {
        _cts.Cancel();
    }
}

/// <summary>
/// Абстракция от RFID-железа (HID/Serial/TCP)
/// </summary>
public class ScannerHardwareService : IDisposable
{
    private SerialPort? _serialPort;
    private TcpClient? _tcpClient;
    private NetworkStream? _stream;
    private CancellationTokenSource? _cts;
    private Task? _readTask;
    private readonly object _lock = new();
    private DateTime _lastTagTime = DateTime.MinValue;

    public event Action<string>? TagReceived;
    public event Action<bool, string>? StatusChanged;

    public bool IsConnected { get; private set; }
    public ScannerMode Mode { get; private set; }

    public enum ScannerMode
    {
        Hid,      // Эмуляция клавиатуры (обрабатывается в UI)
        Tcp,      // TCP/IP сокет
        Serial    // RS232
    }

    public async Task<bool> ConnectTcpAsync(string ip, int port, CancellationToken ct = default)
    {
        try
        {
            await DisconnectAsync();
            _tcpClient = new TcpClient();
            await _tcpClient.ConnectAsync(ip, port, ct);
            _stream = _tcpClient.GetStream();
            _cts = new CancellationTokenSource();
            _readTask = Task.Run(() => ReadTcpLoop(_cts.Token));
            Mode = ScannerMode.Tcp;
            IsConnected = true;
            StatusChanged?.Invoke(true, $"Подключено к {ip}:{port}");
            return true;
        }
        catch
        {
            IsConnected = false;
            StatusChanged?.Invoke(false, "Ошибка подключения");
            return false;
        }
    }

    public async Task<bool> ConnectSerialAsync(string portName, int baudRate = 9600)
    {
        try
        {
            await DisconnectAsync();
            _serialPort = new SerialPort(portName, baudRate)
            {
                ReadTimeout = 1000,
                WriteTimeout = 1000,
                NewLine = "\r\n"
            };
            _serialPort.Open();
            Mode = ScannerMode.Serial;
            IsConnected = true;
            StatusChanged?.Invoke(true, $"Порт {portName} открыт");
            return true;
        }
        catch
        {
            IsConnected = false;
            StatusChanged?.Invoke(false, "Ошибка порта");
            return false;
        }
    }

    private void ReadTcpLoop(CancellationToken ct)
    {
        var buffer = new byte[4096];
        var tagBuffer = new System.Text.StringBuilder();

        while (!ct.IsCancellationRequested && _stream != null && _stream.CanRead)
        {
            try
            {
                var bytesRead = _stream.Read(buffer, 0, buffer.Length);
                if (bytesRead == 0) break;

                for (int i = 0; i < bytesRead; i++)
                {
                    var b = buffer[i];
                    if (b == 0x0D || b == 0x0A)
                    {
                        var tag = tagBuffer.ToString().Trim();
                        if (tag.Length > 0)
                            OnTagReceived(tag);
                        tagBuffer.Clear();
                    }
                    else if (b >= 0x20 && b <= 0x7E)
                    {
                        tagBuffer.Append((char)b);
                    }
                }
            }
            catch (OperationCanceledException) { break; }
            catch { }
        }
    }

    public void AddChar(char c)
    {
        // Для HID-режима (клавиатура)
        if (c == '\r' || c == '\n')
        {
            // Тег завершён — обрабатывается в ViewModel
        }
    }

    private void OnTagReceived(string tag)
    {
        if ((DateTime.Now - _lastTagTime).TotalMilliseconds < 50)
            return;
        _lastTagTime = DateTime.Now;
        TagReceived?.Invoke(tag);
    }

    public async Task DisconnectAsync()
    {
        _cts?.Cancel();
        _readTask?.Wait(1000);
        _stream?.Close();
        _tcpClient?.Close();
        _serialPort?.Close();
        _serialPort?.Dispose();
        _tcpClient?.Dispose();
        _stream = null;
        _tcpClient = null;
        _serialPort = null;
        _cts?.Dispose();
        _cts = null;
        IsConnected = false;
        Mode = 0;
        StatusChanged?.Invoke(false, "Отключено");
    }

    public void Dispose()
    {
        _cts?.Cancel();
        _readTask?.Wait(500);
        _stream?.Close();
        _tcpClient?.Close();
        _serialPort?.Close();
        _serialPort?.Dispose();
        _tcpClient?.Dispose();
        _cts?.Dispose();
    }
}
