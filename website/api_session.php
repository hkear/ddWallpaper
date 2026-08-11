<?php
/**
 * AJAX Session handler - stores JWT token in PHP session
 */
session_start();
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $_SESSION['token'] = $_POST['token'] ?? '';
    echo 'ok';
}
