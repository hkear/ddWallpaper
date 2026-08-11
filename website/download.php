<?php
/**
 * 下载代理 - 无需 CORS，支持 token 传参
 * 用法: /download.php?id=123&token=xxx
 */
require_once __DIR__ . '/config.php';

$id = (int)($_GET['id'] ?? 0);
$token = $_GET['token'] ?? '';
if (!$id || !$token) { http_response_code(400); exit; }

// 通过 API 下载，带上 Authorization 头
$url = API_BASE . "/wallpapers/$id/download";
$ch = curl_init($url);
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_FOLLOWLOCATION => true,
    CURLOPT_MAXREDIRS => 5,
    CURLOPT_TIMEOUT => 60,
    CURLOPT_HTTPHEADER => ["Authorization: Bearer $token"],
]);
$data = curl_exec($ch);
$http = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$type = curl_getinfo($ch, CURLINFO_CONTENT_TYPE);
curl_close($ch);

if ($http != 200 || $data === false) {
    http_response_code(500);
    exit;
}

header("Content-Type: $type");
header("Content-Disposition: attachment; filename=\"wallpaper-$id.jpg\"");
header("Content-Length: " . strlen($data));
echo $data;
