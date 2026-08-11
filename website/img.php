<?php
/**
 * 图片代理 - 隐藏OSS真实URL
 * 用法: /img.php?id=123&size=thumb|720|1080|origin
 */
require_once __DIR__ . '/config.php';

$id = (int)($_GET['id'] ?? 0);
$size = $_GET['size'] ?? 'thumb';
if (!$id) { http_response_code(404); exit; }

// 从API获取壁纸信息
$json = api_get("/wallpapers/$id");
if (!$json) { http_response_code(404); exit; }
$wp = json_decode($json, true);
if (!$wp || empty($wp['original_url'])) { http_response_code(404); exit; }

// 根据size选择URL
switch ($size) {
    case 'origin': $url = $wp['original_url']; break;
    case '1080':   $url = $wp['thumbnail_1080_url'] ?? $wp['original_url']; break;
    case '720':    $url = $wp['thumbnail_720_url'] ?? $wp['thumbnail_small_url'] ?? $wp['original_url']; break;
    case 'thumb':
    default:       $url = $wp['thumbnail_small_url'] ?? $wp['thumbnail_720_url'] ?? $wp['original_url']; break;
}

if (!$url) { http_response_code(404); exit; }

// 非登录用户只能看缩略图
if ($size !== 'thumb' && !is_logged_in()) {
    $url = $wp['thumbnail_small_url'] ?? $wp['thumbnail_720_url'] ?? $wp['original_url'];
}

// 获取图片并输出
$ch = curl_init($url);
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_FOLLOWLOCATION => true,
    CURLOPT_TIMEOUT => 30,
    CURLOPT_USERAGENT => 'WallpaperSite/1.0',
]);
$data = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$content_type = curl_getinfo($ch, CURLINFO_CONTENT_TYPE);
curl_close($ch);

if ($http_code !== 200 || $data === false) {
    http_response_code(502);
    exit;
}

header("Content-Type: $content_type");
header("Cache-Control: public, max-age=86400");
echo $data;
