<?php
define('API_BASE', 'https://api.ddbz.art/api/v1');
define('SITE_NAME', '多点壁纸');
define('LOGO_PATH', 'https://pc.ddbz.art/static/images/logo.png');
define('APP_URL', 'https://pc.ddbz.art');

// Start session for login
session_start();

function is_logged_in() {
    return !empty($_SESSION['token']);
}

function api_get($path, $token = null) {
    $opts = ['http' => ['method' => 'GET', 'header' => 'User-Agent: WallpaperSite/1.0']];
    if ($token) $opts['http']['header'] .= "\r\nAuthorization: Bearer $token";
    return @file_get_contents(API_BASE . $path, false, stream_context_create($opts));
}

function api_post($path, $data, $token = null) {
    $opts = [
        'http' => [
            'method' => 'POST',
            'header' => "Content-Type: application/x-www-form-urlencoded\r\nUser-Agent: WallpaperSite/1.0",
            'content' => http_build_query($data),
        ]
    ];
    if ($token) $opts['http']['header'] .= "\r\nAuthorization: Bearer $token";
    return @file_get_contents(API_BASE . $path, false, stream_context_create($opts));
}
