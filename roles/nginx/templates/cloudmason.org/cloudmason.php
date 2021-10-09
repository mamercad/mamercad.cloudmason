<?php
if ($_SERVER['REQUEST_METHOD'] == 'POST') {
  $payload = json_decode(file_get_contents('php://input'), true);
  if (isset($payload['ref']) && $payload['ref'] == 'refs/heads/main') {
    exec("echo == $(date) == >>./webhook.log && git pull origin main >>./webhook.log 2>&1");
  }
}
?>
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <meta name="description" content="">
    <meta name="author" content="Mark Otto, Jacob Thornton, and Bootstrap contributors">
    <meta name="generator" content="Jekyll v4.1.1">
    <title>Cloudmason</title>

    <link rel="apple-touch-icon" sizes="180x180" href ="/apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href ="/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href ="/favicon-16x16.png">
    <link rel="manifest" href="/site.webmanifest">

    <link rel="canonical" href="https://getbootstrap.com/docs/4.5/examples/starter-template/">

    <!-- Global site tag (gtag.js) - Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=UA-49577207-1"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'UA-49577207-1');
    </script>

    <!-- Bootstrap core CSS -->
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" integrity="sha384-JcKb8q3iqJ61gNV9KGb8thSsNjpSL0n8PARn9HuZOnIxN0hoP+VmmDGMN5t9UJ0Z" crossorigin="anonymous">

    <style>
      .bd-placeholder-img {
        font-size: 1.125rem;
        text-anchor: middle;
        -webkit-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
        user-select: none;
      }

      @media (min-width: 768px) {
        .bd-placeholder-img-lg {
          font-size: 3.5rem;
        }
      }
    </style>
    <style>
      body {
        padding-top: 5rem;
      }
      .starter-template {
        padding: 3rem 1.5rem;
        text-align: left;
      }
    </style>
  </head>
  <body>
    <nav class="navbar navbar-expand-md navbar-dark bg-dark fixed-top">
  <a class="navbar-brand" href="#">Cloudmason</a>
  <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarsExampleDefault" aria-controls="navbarsExampleDefault" aria-expanded="false" aria-label="Toggle navigation">
    <span class="navbar-toggler-icon"></span>
  </button>

  <div class="collapse navbar-collapse" id="navbarsExampleDefault">
    <ul class="navbar-nav mr-auto">
      <li class="nav-item active"><a class="nav-link" href="index.php">Home <span class="sr-only">(current)</span></a></li>
      <!-- <li class="nav-item"><a class="nav-link" href="graphs.php">Graphs</a></li> -->
      <!-- <li class="nav-item"><a class="nav-link" href="media.php">Media</a></li> -->
      <!-- <li class="nav-item"><a class="nav-link" href="/prometheus">Prometheus</a></li> -->
      <!-- <li class="nav-item"><a class="nav-link" href="/grafana">Grafana</a></li> -->
      <!-- <li class="nav-item"><a class="nav-link" href="/sabnzbd">Sabnzbd</a></li> -->
      <li class="nav-item"><a class="nav-link" href="https://github.com/mamercad/">GitHub</a></li>
      <li class="nav-item"><a class="nav-link" href="https://mamercad.github.io/">Blog</a></li>
      <li class="nav-item"><a class="nav-link" href="https://cloudkey.cloudmason.org:8443/">UniFi</a></li>
      <li class="nav-item"><a class="nav-link" href="https://dash.cloudflare.com/">Cloudflare</a></li>
      <li class="nav-item"><a class="nav-link" href="https://login.tailscale.com/">Tailscale</a></li>
      <li class="nav-item"><a class="nav-link" href="weather.php">PWS</a></li>
    </ul>
    <form class="form-inline my-2 my-lg-0">
      <img src="https://healthchecks.io/badge/5dc9afdd-f4da-4b74-bb83-84430f/_JD3lXcF.svg">
    </form>
<!--
      <li class="nav-item">
        <a class="nav-link disabled" href="#" tabindex="-1" aria-disabled="true">Disabled</a>
      </li>
      <li class="nav-item dropdown">
        <a class="nav-link dropdown-toggle" href="#" id="dropdown01" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">Dropdown</a>
        <div class="dropdown-menu" aria-labelledby="dropdown01">
          <a class="dropdown-item" href="#">Action</a>
          <a class="dropdown-item" href="#">Another action</a>
          <a class="dropdown-item" href="#">Something else here</a>
        </div>
      </li>
    </ul>
-->
<!--
    <form class="form-inline my-2 my-lg-0">
      <input class="form-control mr-sm-2" type="text" placeholder="Search" aria-label="Search">
      <button class="btn btn-secondary my-2 my-sm-0" type="submit">Search</button>
    </form>
  </div>
-->
</nav>

<main role="main" class="container">

  <div class="starter-template">
<h1>Chop wood, carry water.</h1>
<br/>
<p class="lead"><?= shell_exec("cat /usr/share/nginx/html/cloudmason.org/cloudmason"); ?></p>
<br/>
<b>$ hostname</b> <?= shell_exec('hostname'); ?><br/>
<b>$ uptime</b> <?= shell_exec('uptime'); ?><br/>
<br/>
<b>$ date</b> <?= shell_exec('date'); ?><br/>
<b>$ date -u</b> <?= shell_exec('date -u'); ?><br/>
<br/>
<b>$ rand</b> <?= rand(); ?><br/>
<b>$ openssl rand -hex 20</b> <?= shell_exec('openssl rand -hex 20'); ?><br/>
<b>$ openesl rand -base64 20</b> <?= shell_exec('openssl rand -base64 20'); ?><br/>
<br/>
<!--
<b>$ f2b-sshd</b><br/><pre><?= shell_exec('cat /usr/share/nginx/html/f2b-sshd'); ?></pre>
<br/>
-->
<b>$ fortune bofh-excuses linuxcookie computers linux</b><br/><pre><?= shell_exec('/usr/games/fortune bofh-excuses linuxcookie computers linux'); ?></pre>
<!--
<? if ($_SERVER['HTTP_X_FORWARDED_SERVER'] == 'net1') { ?>
<b>$ sshbrutes.sh</b><br/><pre><?= shell_exec('cat /usr/share/nginx/html/cloudmason.org/sshbrutes'); ?></pre>
<? } ?>
-->
<br/>
<!--
<b>$ git log -1</b><br/><pre><?= shell_exec('git log -1'); ?></pre>
-->

<a href="https://www.digitalocean.com/?refcode=86a7236d915c&utm_campaign=Referral_Invite&utm_medium=Referral_Program&utm_source=badge"><img src="https://web-platforms.sfo2.digitaloceanspaces.com/WWW/Badge%203.svg" alt="DigitalOcean Referral Badge" /></a>

  </div>


</main><!-- /.container -->
<script src="https://code.jquery.com/jquery-3.5.1.slim.min.js" integrity="sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj" crossorigin="anonymous"></script>
<script>window.jQuery || document.write('<script src="../assets/js/vendor/jquery.slim.min.js"><\/script>')</script><script src="../assets/dist/js/bootstrap.bundle.min.js"></script>
</html>
