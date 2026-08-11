<?php
/**
 * ddWallpaper 反馈表单处理
 * 接收网站 contact 表单 POST，转发到 FastAPI /api/v1/feedback
 */
header('Content-Type: application/json; charset=utf-8');

// API 地址
define('API_URL', 'http://localhost:8082/api/v1/feedback');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['detail' => 'Method Not Allowed'], JSON_UNESCAPED_UNICODE);
    exit;
}

// 获取表单数据
$name    = trim($_POST['name']    ?? '');
$email   = trim($_POST['email']   ?? '');
$message = trim($_POST['message'] ?? '');

// 基本校验
$errors = [];
if ($name === '') {
    $errors[] = '请输入姓名';
}
if ($email === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    $errors[] = '请输入有效的邮箱地址';
}
if ($message === '') {
    $errors[] = '请输入反馈内容';
}
if (mb_strlen($message) > 2000) {
    $errors[] = '反馈内容不能超过2000字';
}

if (!empty($errors)) {
    http_response_code(422);
    echo json_encode(['detail' => $errors], JSON_UNESCAPED_UNICODE);
    exit;
}

// 转发到 FastAPI
$payload = json_encode([
    'name'    => $name,
    'email'   => $email,
    'message' => $message,
], JSON_UNESCAPED_UNICODE);

$ch = curl_init(API_URL);
curl_setopt_array($ch, [
    CURLOPT_POST           => true,
    CURLOPT_POSTFIELDS     => $payload,
    CURLOPT_HTTPHEADER     => [
        'Content-Type: application/json',
        'Accept: application/json',
    ],
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT        => 15,
    CURLOPT_CONNECTTIMEOUT => 5,
]);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$error    = curl_error($ch);
curl_close($ch);

if ($error) {
    http_response_code(502);
    echo json_encode(['detail' => '提交失败，请稍后重试'], JSON_UNESCAPED_UNICODE);
    exit;
}

http_response_code($httpCode >= 200 && $httpCode < 300 ? 200 : $httpCode);
echo $response;
