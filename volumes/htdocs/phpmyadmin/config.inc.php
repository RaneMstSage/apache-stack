<?php
/* vim: set expandtab sw=4 ts=4 sts=4: */
/**
 * phpMyAdmin sample configuration, you can use it as base for
 * manual configuration.
 *
 * For easier configuration, use setup/
 */

declare(strict_types=1);

/**
 * This is needed for cookie based authentication to encrypt the cookie.
 * Needs to be a 32-bytes long string of random bytes.
 * You can use: openssl rand -hex 16
 */
$cfg['blowfish_secret'] = 'your_secure_blowfish_secret_here'; // Replace with your own secure key

/**
 * Servers configuration
 */
$i = 0;

/**
 * First server
 */
$i++;
/* Authentication type */
$cfg['Servers'][$i]['auth_type'] = 'cookie';
/* Server parameters */
$cfg['Servers'][$i]['host'] = 'mysql';  // Using the Docker service name
$cfg['Servers'][$i]['compress'] = false;
$cfg['Servers'][$i]['AllowNoPassword'] = false;

/**
 * phpMyAdmin configuration storage settings.
 */
$cfg['Servers'][$i]['controlhost'] = 'mysql';
$cfg['Servers'][$i]['controlport'] = '';
$cfg['Servers'][$i]['controluser'] = 'pma';
$cfg['Servers'][$i]['controlpass'] = 'your_pma_password';  // Replace with secure password

/* Storage database and tables */
$cfg['Servers'][$i]['pmadb'] = 'phpmyadmin';
$cfg['Servers'][$i]['bookmarktable'] = 'pma__bookmark';
$cfg['Servers'][$i]['relation'] = 'pma__relation';
$cfg['Servers'][$i]['table_info'] = 'pma__table_info';
$cfg['Servers'][$i]['table_coords'] = 'pma__table_coords';
$cfg['Servers'][$i]['pdf_pages'] = 'pma__pdf_pages';
$cfg['Servers'][$i]['column_info'] = 'pma__column_info';
$cfg['Servers'][$i]['history'] = 'pma__history';
$cfg['Servers'][$i]['table_uiprefs'] = 'pma__table_uiprefs';
$cfg['Servers'][$i]['tracking'] = 'pma__tracking';
$cfg['Servers'][$i]['userconfig'] = 'pma__userconfig';
$cfg['Servers'][$i]['recent'] = 'pma__recent';
$cfg['Servers'][$i]['favorite'] = 'pma__favorite';
$cfg['Servers'][$i]['users'] = 'pma__users';
$cfg['Servers'][$i]['usergroups'] = 'pma__usergroups';
$cfg['Servers'][$i]['navigationhiding'] = 'pma__navigationhiding';
$cfg['Servers'][$i]['savedsearches'] = 'pma__savedsearches';
$cfg['Servers'][$i]['central_columns'] = 'pma__central_columns';
$cfg['Servers'][$i]['designer_settings'] = 'pma__designer_settings';
$cfg['Servers'][$i]['export_templates'] = 'pma__export_templates';

/**
 * End of servers configuration
 */

/**
 * Directories for saving/loading files from server
 */
$cfg['UploadDir'] = '';
$cfg['SaveDir'] = '';

/**
 * Security features
 */
$cfg['LoginCookieValidity'] = 1440; // Limit cookie validity to 1 day
$cfg['LoginCookieStore'] = 0;       // Don't store login cookie permanently
$cfg['LoginCookieDeleteAll'] = true; // Delete all cookies on logout
$cfg['AllowArbitraryServer'] = false; // Disable arbitrary server connections
$cfg['ExecTimeLimit'] = 600;        // Limit execution time for long-running scripts

/**
 * Recommended settings for improved security
 */
$cfg['CheckConfigurationPermissions'] = false; // Don't check file permissions for config.inc.php
$cfg['AllowUserDropDatabase'] = false; // Prevent users from dropping databases
$cfg['DefaultConnectionCollation'] = 'utf8mb4_unicode_ci'; // Better collation support

/**
 * Theme settings
 */
$cfg['ThemeDefault'] = 'pmahomme';