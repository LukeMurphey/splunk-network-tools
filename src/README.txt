================================================
Overview
================================================

This app provides a series of tools for troubleshooting networks.



================================================
Configuring Splunk
================================================
Install this app into Splunk by doing the following:

  1. Log in to Splunk Web and navigate to "Apps » Manage Apps" via the app dropdown at the top left of Splunk's user interface
  2. Click the "install app from file" button
  3. Upload the file by clicking "Choose file" and selecting the app
  4. Click upload
  5. Restart Splunk if a dialog asks you to

Once the app is installed, you can use can open the "Network Toolkit" app from the main launcher.



================================================
Getting Support
================================================

Go to the following website if you need support and start a question:

     https://answers.splunk.com/app/questions/3491.html

You can access the source-code and get technical details about the app at:

     https://github.com/LukeMurphey/splunk-network-tools

You can also contact me via one of the following means:

 1) Send me an email: Luke@Lukemurphey.net
 2) Talk to me on the Slack group splunk-usergroups. You can direct message me @lukemurphey.



================================================
Change History
================================================

+---------+------------------------------------------------------------------------------------------------------------------+
| Version |  Changes                                                                                                         |
+---------+------------------------------------------------------------------------------------------------------------------+
| 0.5     | Initial release                                                                                                  |
|---------|------------------------------------------------------------------------------------------------------------------|
| 0.6     | Added Windows support for the traceroute command                                                                 |
|         | Fixed excessive CPU usage on the wake-on-LAN dashboard                                                           |
|         | Fixed execute button which was on the wrong line on Splunk 6.4                                                   |
|---------|------------------------------------------------------------------------------------------------------------------|
| 0.7     | Fixed issue where some invalid MAC addresses were accepted on the Wake-on-LAN page                               |
|         | Fixed dialog on Wake-on-LAN page that would sometimes act as if the input was invalid when it wasn't             |
|         | Fixed issue where users could sort the actions column on the wake-on-LAN dashboard                               |
|---------|------------------------------------------------------------------------------------------------------------------|
| 0.8     | You can now globally define a default index for results to go into                                               |
|         | nslookup now supports reverse DNS lookups                                                                        |
|---------|------------------------------------------------------------------------------------------------------------------|
| 0.9     | Fixed issue where the setup page didn't recognize that you had completed setup already                           |
|---------|------------------------------------------------------------------------------------------------------------------|
| 0.10    | Fixed issue where the app could break the Website Input app                                                      |
|         | Improved compatibility with Splunk 6.6                                                                           |
|         | Added workflow actions for performing operations on hosts from the search view                                   |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.0     | Added modular input for scheduling Internet connection speedtests                                                |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.1     | Added lookup commands for performing operations on results (see http://bit.ly/2uHxRm8)                           |
|         | Fixed issue where hosts we sometimes displayed as online on the wake-on-lan list when they were not              |
|         | Fixed issue where unnecessary fields showed up on the whois dashboard                                            |
+---------+------------------------------------------------------------------------------------------------------------------+
