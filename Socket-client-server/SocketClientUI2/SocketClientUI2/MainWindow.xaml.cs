using Microsoft.Win32;
using System.Net.Sockets;
using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using System.IO;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Diagnostics;
using System.Text.Encodings.Web;

namespace SocketClientUI2
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        private TcpClient _tcpClient;
        private NetworkStream _stream;

        public MainWindow()
        {
            InitializeComponent();
        }

        private void Connect_Click(object sender, RoutedEventArgs e)
        {
            if (_tcpClient == null || !_tcpClient.Connected)
            {
                try
                {
                    _tcpClient = new TcpClient("localhost", 8080);
                    _stream = _tcpClient.GetStream();
                    ConnectButton.Content = "Disconnect";
                    SendButton.IsEnabled = true;
                    PublishButton.IsEnabled = true;
                }
                catch (Exception ex)
                {
                    MessageBox.Show("Connection failed: " + ex.Message);
                }
            }
            else
            {
                _tcpClient.Close();
                _tcpClient = null;
                ConnectButton.Content = "Connect";
                SendButton.IsEnabled = false;
                PublishButton.IsEnabled = false;
            }
        }

        private void Send_Click(object sender, RoutedEventArgs e)
        {
            if (_tcpClient != null && _tcpClient.Connected)
            {
                string inputText = MessageInput.Text.Trim();

                if (inputText.StartsWith('{'))
                {
                    try
                    {
                        // Trying to format as proper JSON first
                        //string formattedJson = FormatAsValidJson(inputText);

                        //// Parsing to validate
                        //JsonDocument.Parse(formattedJson);

                        //// Wrapping in array for server
                        //string jsonArray = $"[{formattedJson}]";
                        //SendFramedMessage(jsonArray);

                        using (JsonDocument doc = JsonDocument.Parse(inputText))
                        {
                            // If it's valid JSON, format it while preserving spaces
                            var options = new JsonSerializerOptions
                            {
                                WriteIndented = false,
                                Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
                            };

                            // Deserialize and serialize to ensure proper JSON structure
                            var jsonElement = doc.RootElement;
                            string formattedJson = JsonSerializer.Serialize(
                                JsonSerializer.Deserialize<dynamic>(inputText),
                                options
                            );

                            // Wrap in array for server
                            string jsonArray = $"[{formattedJson}]";
                            SendFramedMessage(jsonArray);
                        }


                        return;
                    }
                    catch (JsonException ex)
                    {
                        MessageBox.Show($"Invalid JSON format: {ex.Message}\n\nPlease ensure property names are in quotes and values are properly formatted.");
                        return;
                    }
                }

                if (!inputText.Contains(','))
                {
                    MessageBox.Show("Invalid CSV format. Ensure the row is comma-separated.");
                    return;
                }

                // Defining a CSV header (modifying according to the server's accepted format)
                string csvData = "SysCode,SysName,DeviceCode,DeviceName,DataExtType,Content,Remark\n" + inputText;
                SendFramedMessage(csvData);



            }
        }

        private void SelectFile_Click(object sender, RoutedEventArgs e)
        {
            OpenFileDialog openFileDialog = new OpenFileDialog
            {
                Filter = "JSON Files (*.json)|*.json|CSV Files (*.csv)|*.csv"
            };
            if (openFileDialog.ShowDialog() == true)
            {
                FilePath.Text = openFileDialog.FileName;
            }
        }

        private void Publish_Click(object sender, RoutedEventArgs e)
        {

            if (!File.Exists(FilePath.Text))
            {
                MessageBox.Show("Please select a valid file first.");
                return;
            }

            try
            {
                // Disabling the publish button during the sending process
                PublishButton.IsEnabled = false;

                string content = File.ReadAllText(FilePath.Text);
                string extension = System.IO.Path.GetExtension(FilePath.Text).ToLower();



                // Validate file content based on type
                if (extension == ".json")
                {
                    try
                    {
                        // Parsing the JSON object
                        using JsonDocument doc = JsonDocument.Parse(content);

                        // Configuring JSON serialization options to preserve spaces
                        var options = new JsonSerializerOptions 
                        {
                            WriteIndented = false,
                            Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
                        };

                        // Checking if content is already an array
                        if (doc.RootElement.ValueKind != JsonValueKind.Array)
                        {
                            var jsonElement = doc.RootElement;
                            string formattedJSON = JsonSerializer.Serialize(JsonSerializer.Deserialize<dynamic>(content), options);

                            // If it's a single object, wrap it in an array
                            content = $"[{formattedJSON}]";

                            
                        }
                        else
                        {
                            // If it's already an array, just reformat it
                            content = JsonSerializer.Serialize(
                                JsonSerializer.Deserialize<dynamic>(content),
                                options
                            );
                        }

                        SendFramedMessage(content);
                        MessageBox.Show("File published successfully!");
                    }
                    catch (JsonException ex)
                    {
                        MessageBox.Show($"Invalid JSON in file: {ex.Message}");
                        return;
                    }
                }
                else if (extension == ".csv")
                {
                    // Validate CSV has at least header and one data row
                    var lines = content.Split('\n')
                        .Select(l => l.Trim())
                        .Where(l => !string.IsNullOrEmpty(l))
                        .ToList();

                    if (lines.Count < 2)
                    {
                        MessageBox.Show("CSV file must contain at least a header row and one data row.");
                        return;
                    }

                    SendFramedMessage(content);
                    MessageBox.Show("File published successfully!");
                }
                else
                {
                    MessageBox.Show("Unsupported file type. Please select a .json or .csv file.");
                    return;
                }

                //// Disable publish button during processing
                //PublishButton.IsEnabled = false;

            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error reading or processing file: {ex.Message}");
            }
            finally
            {
                PublishButton.IsEnabled = true;
            }
        }

        private void SendFramedMessage(string message)
        {
            if (_tcpClient == null || !_tcpClient.Connected)
            {
                throw new InvalidOperationException("Not connected to server");
            }

            try
            {
                // Convert message to UTF-8 bytes
                byte[] messageBytes = Encoding.UTF8.GetBytes(message);

                // Create length prefix (4 bytes, big-endian)
                byte[] lengthPrefix = BitConverter.GetBytes(messageBytes.Length);
                if (BitConverter.IsLittleEndian)
                {
                    Array.Reverse(lengthPrefix);
                }

                // Log the message being sent
                Debug.WriteLine($"[{DateTime.UtcNow:yyyy-MM-dd HH:mm:ss}] Sending message with length: {messageBytes.Length}");
                Debug.WriteLine($"[{DateTime.UtcNow:yyyy-MM-dd HH:mm:ss}] Message content: {message}");

                //// Send in a single write to avoid fragmentation
                //byte[] completeMessage = new byte[4 + messageBytes.Length];
                //lengthPrefix.CopyTo(completeMessage, 0);
                //messageBytes.CopyTo(completeMessage, 4);

                // Send length prefix first
                _stream.Write(lengthPrefix, 0, 4);
                _stream.Flush();

                // Then send the actual message
                _stream.Write(messageBytes, 0, messageBytes.Length);
                _stream.Flush();

                //_stream.Write(completeMessage, 0, completeMessage.Length);
                //_stream.Flush();

                Debug.WriteLine($"[{DateTime.UtcNow:yyyy-MM-dd HH:mm:ss}] Message sent successfully");
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"[{DateTime.UtcNow:yyyy-MM-dd HH:mm:ss}] Error sending message: {ex.Message}");
                throw;
            }

            // Creating the complete message in memory first
            //using (MemoryStream memoryStream = new MemoryStream())
            //{
            //    byte[] messageBytes = Encoding.UTF8.GetBytes(message);
            //    byte[] lengthPrefix = BitConverter.GetBytes(messageBytes.Length);

            //    if (BitConverter.IsLittleEndian)
            //    {
            //        // Converting to big-edian
            //        Array.Reverse(lengthPrefix);
            //    }

            //    memoryStream.Write(lengthPrefix, 0, 4);
            //    memoryStream.Write(messageBytes, 0, messageBytes.Length);

            //    // Sending the complete buffer in one go
            //    byte[] completeMessage = memoryStream.ToArray();
            //    _stream.Write(completeMessage, 0, completeMessage.Length);
            //    _stream.Flush();
            //}
        }

        private string FormatAsValidJson(string input)
        {
            // Remove any whitespace around structural characters, preserving spaces in values
            input = Regex.Replace(input, @"\s*([\[\]\{\},:])\s*", "$1");

            // Add quotes to property names if missing
            input = Regex.Replace(input, @"(\{|,)(\w+):", "$1\"$2\":");

            // Ensure proper spacing after colons for readability
            // input = Regex.Replace(input, @":(?!""|[0-9]|\{|\[)", ": ");
            input = Regex.Replace(input, @":(?!(\s*[""{[\d]))", ": ");

            return input;
        }
    }
}