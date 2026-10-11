using System.IO.Ports;
using System.Net.Sockets;

namespace RfidScanner.Services;

/// <summary>
/// Событие: получена RFID-метка
/// </summary>
public class RfidTagReceivedEventArgs : EventArgs
{
    public string Tag { get; }
    public DateTime Timestamp { get; }

    public RfidTagReceivedEventArgs(string tag)
    {
        Tag = tag;
        Timestamp = DateTime.Now;
    }
}

/// <summary>
/// Событие: статус сканера
/// </summary>
public class ScannerStatusChangedEventArgs : EventArgs
{
    public bool IsConnected { get; }
    public string Message { get; }

    public ScannerStatusChangedEventArgs(bool isConnected, string message)
    {
        IsConnected = isConnected;
        Message = message;
    }
}

/// <summary>
/// Сервис сканера — поддержка HID и TCP режимов
/// </summary>
public class ScannerService : IDisposable
{
    private SerialPort? _serialPort;
    private TcpClient? _tcpClient;
    private NetworkStream? _stream;
    private CancellationTokenSource? _cts;
    private Task? _readTask;
    private readonly object _lock = new();
    private DateTime _lastTagTime = DateTime.MinValue;

    public event EventHandler<RfidTagReceivedEventArgs>? TagReceived;
    public event EventHandler<ScannerStatusChangedEventArgs>? StatusChanged;

    public bool IsConnected { get; private set; }
    public ScannerMode Mode { get; private set; }

    // ==================== HID режим (клавиатура) ====================
    // HID-режим обрабатывается на уровне UI (MainWindow.KeyDown)
    // Этот метод вызывается из UI при получении символа
    public string? ProcessHidKey(char key)
    {
        // RFID-сканер как клавиатура: вводит tag + Enter
        // Просто возвращаем символ — сборка тега происходит в ViewModel
        return key.ToString();
    }

    // ==================== TCP режим ====================

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
            OnStatusChanged(true, $"Подключено к {ip}:{port}");

            return true;
        }
        catch (Exception ex)
        {
            IsConnected = false;
            OnStatusChanged(false, $"Ошибка подключения: {ex.Message}");
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
                if (bytesRead == 0) break; // disconnected

                for (int i = 0; i < bytesRead; i++)
                {
                    var b = buffer[i];

                    // RFID-теги обычно заканчиваются на \r или \n
                    if (b == 0x0D || b == 0x0A)
                    {
                        var tag = tagBuffer.ToString().Trim();
                        if (tag.Length > 0)
                            OnTagReceived(tag);
                        tagBuffer.Clear();
                    }
                    else if (b >= 0x20 && b <= 0x7E) // printable ASCII
                    {
                        tagBuffer.Append((char)b);
                    }
                }
            }
            catch (OperationCanceledException)
            {
                break;
            }
            catch (Exception)
            {
                // Ignore read errors, loop will check connection
            }
        }
    }

    // ==================== Serial режим (RS232) ====================

    public async Task<bool> ConnectSerialAsync(string portName, int baudRate = 9600, CancellationToken ct = default)
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

            _serialPort.DataReceived += OnSerialDataReceived;
            _serialPort.Open();

            Mode = ScannerMode.Tcp; // Serial тоже использует буфер
            IsConnected = true;
            OnStatusChanged(true, $"Порт {portName} открыт");

            return true;
        }
        catch (Exception ex)
        {
            IsConnected = false;
            OnStatusChanged(false, $"Ошибка порта: {ex.Message}");
            return false;
        }
    }

    private void OnSerialDataReceived(object sender, SerialDataReceivedEventArgs e)
    {
        if (_serialPort == null) return;

        var buffer = _serialPort.ReadExisting();
        foreach (var c in buffer)
        {
            if (c == '\r' || c == '\n')
            {
                // Serial данные уже собраны, просто триггерим
            }
        }
    }

    // ==================== Управление ====================

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
        OnStatusChanged(false, "Отключено");
    }

    // ==================== Helpers ====================

    private void OnTagReceived(string tag)
    {
        // Debounce — игнорируем дубликаты < 50мс
        if ((DateTime.Now - _lastTagTime).TotalMilliseconds < 50)
            return;
        _lastTagTime = DateTime.Now;

        TagReceived?.Invoke(this, new RfidTagReceivedEventArgs(tag));
    }

    private void OnStatusChanged(bool connected, string message)
    {
        StatusChanged?.Invoke(this, new ScannerStatusChangedEventArgs(connected, message));
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
        GC.SuppressFinalize(this);
    }
}
