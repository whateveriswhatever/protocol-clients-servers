   M S B A M L   `   `   `  ����J  FWPF-MQTT-Client, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null1clr-namespace:WPF_MQTT_ClientWPF_MQTT_Client  5   	        WPF_MQTT_Client.MainWindow   5   	   W SPresentationCore, Version=9.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35\ XPresentationFramework, Version=9.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35e aSystem.Windows.Controls.Ribbon, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089R NWindowsBase, Version=9.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35^ ZWindowsFormsIntegration, Version=9.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35H 9http://schemas.microsoft.com/winfx/2006/xaml/presentation      5   	   R NSystem.Xaml, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089:x,http://schemas.microsoft.com/winfx/2006/xaml     5   	   @d2http://schemas.microsoft.com/expression/blend/2008     5   	   Jmc;http://schemas.openxmlformats.org/markup-compatibility/2006     5   	   /localclr-namespace:WPF_MQTT_Client     5   	     � Title$  
MainWindow��5   	   $	��450��6   $	��800��6)   .��5	      � $��10q�6    � RowDefinitions 5
   
   �� 5      $
��Auto �6   �� 5      $��* �6   �� 5      $
��Auto �6   .+�5   
   �� $��Connection Settings��6   $��0��60   $��0,0,0,10q�6=   .��5      � $��5q�6    � ColumnDefinitions 5      �� 5      $
��Auto �6'   �� 5      $��* �6'   �� 5      $
��Auto �6'   �� 5      $��* �6'    5      �� 5      $
��Auto �6$   �� 5      $
��Auto �6$   .+�5      �� $��Broker Address:��6   $��0��62   $��0��6?   $��0,0,5,0q�6O   �� 5      -   5         ��Name$ BrokerTextBox��5      $��0��61   $��1��6>   $��0,0,10,0q�6N   $��	localhost��6`   �� 5!      $��Port:��6   $��0��6(   $��2��65   $��0,0,5,0q�6E   �� 5"      -   5        $ PortTextBox��5"      $��0��6/   $��3��6<   $
��1883��6L   �� 5$      $��Topic:��6   $��1��6)   $��0��66   $��0,5,5,0q�6F   �� 5%      -   5        $ TopicTextBox��5%      $��1��60   $��1��6=   $��0,5,10,0q�6M   $��
test/topic��6_   �� 5'      -   5         ��Name$ ConnectButton��5'      $��Connect��60   $��1��6B   $��2��6O   $��2��5(      $��0,5,0,0q�6-   $
��20,5q�6>   6M   5)      5*      �� 5-   
   $��
Data Input��6   $��1��6'   $��0,0,0,10q�64   .��5.      � $��5q�6    5/      �� 50      $
��Auto �6$   �� 51      $��* �6$   �� 52      $
��Auto �6$   .+�55      �� $��0��6    �� Orientation$ 
Horizontal=�6*   $��0,0,0,5q�6C   .+�56      �� $��Data Format:��6   	� 57      -   5         	�Name$ JsonRadioButton��57   "   $
��JSON��6;    d� 	IsChecked$
 TrueY�6J   $��	10,5,20,0q�6[   	� 58      -   5        $ CsvRadioButton��58   "   $	��CSV��6:   $��0,5,0,0q�6H   59      �� 5;      -   5        $ DataTextBox��5;      $��1��6/    �� TextWrapping$
 Wrap=�6<   	 �� AcceptsReturn$
	 True��6P   "
 �� VerticalScrollBarVisibility$

 Auto=�5<      $��0,0,0,5q�6=   �� 5>      $��2��6   $ 
Horizontal=�6*   $��Right=�6C   .+�5?      �� -   5        $ UploadButton��5?      $��Upload File��63   $��0,0,10,0q�6I   $
��20,5q�5@      6,   �� 5A      -	   5        $ PublishFileButton��5A      $��Publish File��68   $
��20,5q�6O   6^   �� 5B      -
   5        $ 
SendButton��5B      $
��Send��61   $
��20,5q�6@   6O   5C      5D      5E      �� 5H   
   $��2��6   .@�5I      �� .��5J      �� -   5         ��Name$ StatusTextBlock��5J      $��Status: Disconnected��65   5K      5L      5M      5N      