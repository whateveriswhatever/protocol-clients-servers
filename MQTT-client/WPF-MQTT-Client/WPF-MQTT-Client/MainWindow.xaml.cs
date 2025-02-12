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
using System.Linq;
using System.IO;
using System.Threading.Tasks;
using MQTTnet;
using Microsoft.Win32;
using System.Text.Json;
using MQTTnet.Extensions.ManagedClient;
using MQTTnet.Protocol;


namespace WPF_MQTT_Client
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        private IMqttClient mqttClient;
        private bool isConnected = false;


        public MainWindow()
        {
            InitializeComponent();
        }

        private void DisableDataControls()
        {
            DataTextBox.IsEnabled = false;
            UploadButton.IsEnabled = false;
            SendButton.IsEnabled = false;
        }

        private void EnableDataControls()
        {
            DataTextBox.IsEnabled = true;
            UploadButton.IsEnabled = true;
            SendButton.IsEnabled = true;
        }

        private async void ConnectButton_Click(object sender, RoutedEventArgs e)
        {
            if (!isConnected)
            {
                await ConnectToMqttBroker();
            }
            else
            {
                await DisconnectFromMqttBroker();
            }
        }

        private async Task ConnectToMqttBroker()
        {
            try
            {
                var factory = new MQTTnet.MqttClientFactory();
                mqttClient = factory.CreateMqttClient();

                var builder = new MqttClientOptionsBuilder()
                    .WithTcpServer(BrokerTextBox.Text, int.Parse(PortTextBox.Text))
                    .WithClientId(Guid.NewGuid().ToString())
                    .WithCleanSession();

                var options = builder.Build();

                // Connecting to broker
                await mqttClient.ConnectAsync(options);

                isConnected = true;
                ConnectButton.Content = "Disconnect";
                StatusTextBlock.Text = "Status: Connected";
                EnableDataControls();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Connection error: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private async Task DisconnectFromMqttBroker()
        {
            if (mqttClient != null && mqttClient.IsConnected)
            {
                await mqttClient.DisconnectAsync();
                isConnected = false;
                ConnectButton.Content = "Connect";
                StatusTextBlock.Text = "Status: Disconnected";
                DisableDataControls();
            }
        }

        private void UploadButton_Click(object sender, RoutedEventArgs e)
        {
            var openFileDialog = new OpenFileDialog
            {
                Filter = "JSON files (*.json)|*.json|CSV files (*.csv)|*.csv|All files (*.*)|*.*"
            };

            if (openFileDialog.ShowDialog() == true)
            {
                try
                {
                    string fileContent = File.ReadAllText(openFileDialog.FileName);
                    DataTextBox.Text = fileContent;

                    // Auto-select format based on file extension
                    string extension = System.IO.Path.GetExtension(openFileDialog.FileName).ToLower();
                    JsonRadioButton.IsChecked = extension == ".json";
                    CsvRadioButton.IsChecked = extension == ".csv";
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Error reading file: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        private async void SendButton_Click(object sender, RoutedEventArgs e)
        {
            if (!isConnected || mqttClient == null)
            {
                MessageBox.Show("Please connect to the broker first.", "Error", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            try
            {
                string messageToSend = DataTextBox.Text.Trim();
                if (JsonRadioButton.IsChecked == true)
                {
                    // Validate JSON
                    JsonDocument.Parse(messageToSend);
                  
                }

                // For single CSV data row, the client will send it in raw plain-text format
                var applicationMessage = new MqttApplicationMessageBuilder()
                    .WithTopic(TopicTextBox.Text)
                    .WithPayload(Encoding.UTF8.GetBytes(messageToSend))
                    .WithQualityOfServiceLevel(MqttQualityOfServiceLevel.AtLeastOnce)
                    .WithRetainFlag(false)
                    .Build();

                

                await mqttClient.PublishAsync(applicationMessage);
                MessageBox.Show("Message sent successfully!", "Success", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (JsonException)
            {
                MessageBox.Show("Invalid JSON format.", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error sending message: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private List<List<string>> ParseCsv(string csvContent)
        {
            var result = new List<List<string>>();
            using (var reader = new StringReader(csvContent))
            {
                string? line;
                while ((line = reader.ReadLine()) != null)
                {
                    if (string.IsNullOrWhiteSpace(line)) continue;

                    // Split by comma, handling quoted values
                    var values = line.Split(',')
                                   .Select(v => v.Trim('"', ' '))
                                   .ToList();
                    result.Add(values);
                }
            }
            return result;
        }

        private async void PublishFileButton_Click(object sender, RoutedEventArgs e)
        {
            var openFileDialog = new OpenFileDialog
            {
                Filter = "JSON files (*.json)|*.json|CSV files (*.csv)|*.csv|All files (*.*)|*.*"
            };

            if (openFileDialog.ShowDialog() == true)
            {
                try
                {
                    string filePath = openFileDialog.FileName;
                    string fileContent = File.ReadAllText(filePath);

                    string extension = System.IO.Path.GetExtension(filePath).ToLower();
                    if (extension == ".json")
                    {
                        await PublishJsonFile(fileContent);
                    }
                    else if (extension == ".csv")
                    {
                        await PublishCsvFile(fileContent);
                    }
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Error processing file: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        private async Task PublishJsonFile(string fileContent)
        {
            try
            {
                var jsonArray = JsonDocument.Parse(fileContent).RootElement.EnumerateArray();
                foreach (var jsonElement in jsonArray)
                {
                    var jsonString = jsonElement.GetRawText();
                    var applicationMessage = new MqttApplicationMessageBuilder()
                        .WithTopic(TopicTextBox.Text)
                        .WithPayload(Encoding.UTF8.GetBytes(jsonString))
                        .WithQualityOfServiceLevel(MqttQualityOfServiceLevel.AtLeastOnce)
                        .WithRetainFlag(false)
                        .Build();

                    await mqttClient.PublishAsync(applicationMessage);
                }
                MessageBox.Show("JSON file published successfully!", "Success", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (JsonException)
            {
                MessageBox.Show("Invalid JSON format in file.", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private async Task PublishCsvFile(string fileContent)
        {
            var csvRows = ParseCsv(fileContent);
            if (csvRows.Count == 0)
            {
                MessageBox.Show("CSV file is empty.", "Error", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var headerRow = csvRows[0];
            var expectedHeaders = new[] { "SysCode", "SysName", "DeviceCode", "DeviceName", "DataExtType", "Content", "Remark" };
            if (!headerRow.SequenceEqual(expectedHeaders))
            {
                MessageBox.Show("CSV header row is invalid. Expected headers: " + string.Join(", ", expectedHeaders), "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                return;
            }

            foreach (var row in csvRows.Skip(1))
            {
                var csvRowString = string.Join(",", row);
                var applicationMessage = new MqttApplicationMessageBuilder()
                    .WithTopic(TopicTextBox.Text)
                    .WithPayload(Encoding.UTF8.GetBytes(csvRowString))
                    .WithQualityOfServiceLevel(MqttQualityOfServiceLevel.AtLeastOnce)
                    .WithRetainFlag(false)
                    .Build();

                await mqttClient.PublishAsync(applicationMessage);
            }
            MessageBox.Show("CSV file published successfully!", "Success", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private List<List<string>> ParseCsvFile(string csvContent)
        {
            var result = new List<List<string>>();
            using (var reader = new StringReader(csvContent))
            {
                string? line;
                while ((line = reader.ReadLine()) != null)
                {
                    if (string.IsNullOrWhiteSpace(line)) continue;

                    // Split by comma, handling quoted values
                    var values = line.Split(',')
                                   .Select(v => v.Trim('"', ' '))
                                   .ToList();
                    result.Add(values);
                }
            }
            return result;
        }

        protected override async void OnClosing(System.ComponentModel.CancelEventArgs e)
        {
            await DisconnectFromMqttBroker();
            base.OnClosing(e);
        }
    }
}