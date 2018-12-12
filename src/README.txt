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
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.1.1   | Fixed some minor styling issues on Splunk 7.0                                                                    |
|         | A more informative message is displayed if a command could not be found                                          |
|         | Improving error messaging when the whois lookup was performed without a host field                               |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.2     | Fixing minor styling issue where an icon was the wrong color                                                     |
|         | Added ability to restrict the index used via a URL parameter; see http://bit.ly/2zqcN67                          |
|         | Fixed an issue where the ping view attempted to run even when no input was provided                              |
|         | Added ping modular input and related dashboards so that you can monitor system uptime                            |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.2.1   | Fixing issue where some needed macros were not included                                                          |
|         | Minor enhancements to the batch input UI                                                                         |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.2.2   | Fixing issue where batch creation of inputs could fail                                                           |
|         | Status overview dashboard now refreshes every 30 seconds                                                         |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.2.3   | Fixing overly conservative domain name validation that rejected some valid domain names                          |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.2.4   | Fixing issue where ping search command was too restrictive with domain name validation                           |
|         | Fixed uptime monitoring failing to record a response when the DNS name cannot be resolved                        |
|         | NSlookup search command now correctly uses the DNS server option                                                 |
|         | Drilldown from the Status Overview dashboard now correctly carries the time-range to the search page             |
|         | Fixed uptime calculation which didn't consider DNS resolution failures as ping failures                          |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.2.5   | Fixing issue where setup page didn't include all indexes                                                         |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.2.6   | Adding contact fields to the whois lookup                                                                        |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.2.7   | Reducing the number of informational log messages                                                                |
|         | Added contact information for the whois command                                                                  |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.2.8   | Fixed speedtest command which no longer worked                                                                   |
|         | Improved styling for Splunk 7.1 and 7.2                                                                          |
+---------+------------------------------------------------------------------------------------------------------------------+
