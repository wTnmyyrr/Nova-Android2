from pathlib import Path
p = Path("/tmp/nova-src/NOVA_v4.0_Complete/app/src/main/assets/index.html")
s = p.read_text(encoding="utf-8")
marker = "state = { ...state, ...JSON.parse(localStorage.getItem(settingsKey) || '{}') };\n} catch {}"
assert marker in s, 'Could not find NOVA settings initialization marker'
s = s.replace(marker, marker + "\n// Preconfigured NOVA Cloudflare AI backend\nif (!state.backendUrl) state.backendUrl = 'https://nova-ai-brain.hy1009568.workers.dev';", 1)
# Native Android voice + external-app actions (file:// WebView has no Web Speech API).
bridge = Path("/tmp/nova-src/NOVA_v4.0_Complete/app/src/main/java/com/nova/companion/NovaAndroidBridge.kt")
bridge.write_text("""package com.nova.companion

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings
import android.speech.RecognizerIntent
import android.speech.tts.TextToSpeech
import android.webkit.JavascriptInterface
import android.widget.Toast
import java.util.Locale

class NovaAndroidBridge(private val context: Context) : TextToSpeech.OnInitListener {
    private var tts: TextToSpeech = TextToSpeech(context, this)
    private var ttsReady = false
    private val packageMap = mapOf(
        "youtube" to "com.google.android.youtube", "whatsapp" to "com.whatsapp",
        "instagram" to "com.instagram.android", "spotify" to "com.spotify.music",
        "google maps" to "com.google.android.apps.maps", "gmail" to "com.google.android.gm",
        "telegram" to "org.telegram.messenger", "amazon" to "in.amazon.mShop.android.shopping",
        "flipkart" to "com.flipkart.android", "play store" to "com.android.vending"
    )
    override fun onInit(status: Int) { ttsReady = status == TextToSpeech.SUCCESS }
    @JavascriptInterface fun speak(text: String, language: String) {
        if (!ttsReady) return
        val locale = if (language == "en") Locale("en", "IN") else Locale("hi", "IN")
        tts.language = locale
        tts.setSpeechRate(0.94f)
        tts.setPitch(1.12f)
        if (Build.VERSION.SDK_INT >= 21) tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "nova_reply")
        else @Suppress("DEPRECATION") tts.speak(text, TextToSpeech.QUEUE_FLUSH, null)
    }
    @JavascriptInterface fun stopSpeaking() { if (ttsReady) tts.stop() }
    @JavascriptInterface fun startVoiceInput(language: String) {
        (context as? MainActivity)?.startNovaVoiceRecognition(language)
    }
    @JavascriptInterface fun openUrl(url: String) {
        try {
  val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
  context.startActivity(intent)
        } catch (_: Exception) { Toast.makeText(context, "App/link open nahi ho paya", Toast.LENGTH_SHORT).show() }
    }
    @JavascriptInterface fun openApp(appKey: String): Boolean {
        val pkg = packageMap[appKey.lowercase().trim()] ?: return false
        val i = context.packageManager.getLaunchIntentForPackage(pkg) ?: return false
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK); context.startActivity(i); return true
    }
    @JavascriptInterface fun startWakeWordService() {
        val i = Intent(context, NovaWakeWordService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) context.startForegroundService(i) else context.startService(i)
    }
    @JavascriptInterface fun stopWakeWordService() { context.stopService(Intent(context, NovaWakeWordService::class.java)) }
    @JavascriptInterface fun toggleFloatingBubble() {
        if (!Settings.canDrawOverlays(context)) {
  Toast.makeText(context, "Please allow Display over other apps for NOVA", Toast.LENGTH_LONG).show()
  context.startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:${context.packageName}")).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
  return
        }
        context.startService(Intent(context, NovaFloatingOverlayService::class.java))
    }
}
""", encoding="utf-8")
activity = Path("/tmp/nova-src/NOVA_v4.0_Complete/app/src/main/java/com/nova/companion/MainActivity.kt")
activity.write_text("""package com.nova.companion

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.speech.RecognizerIntent
import android.webkit.*
import androidx.activity.ComponentActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import org.json.JSONObject

class MainActivity : ComponentActivity() {
    private lateinit var webView: WebView
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED)
  ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.RECORD_AUDIO), 100)
        webView = WebView(this)
        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        webView.settings.mediaPlaybackRequiresUserGesture = false
        webView.settings.allowFileAccess = true
        webView.webChromeClient = object : WebChromeClient() {
  override fun onPermissionRequest(request: PermissionRequest) { runOnUiThread { request.grant(request.resources) } }
        }
        webView.webViewClient = object : WebViewClient() {
  override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
      val url = request?.url?.toString() ?: return false
      if (url.startsWith("file:///android_asset/")) return false
      try { startActivity(Intent(Intent.ACTION_VIEW, android.net.Uri.parse(url))) } catch (_: Exception) {}
      return true
  }
        }
        webView.addJavascriptInterface(NovaAndroidBridge(this), "NovaAndroidBridge")
        setContentView(webView)
        webView.loadUrl("file:///android_asset/index.html")
    }
    fun startNovaVoiceRecognition(language: String) {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
  ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.RECORD_AUDIO), 100)
  return
        }
        try {
  val i = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
      putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
      putExtra(RecognizerIntent.EXTRA_LANGUAGE, if (language == "en") "en-IN" else "hi-IN")
      putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, if (language == "en") "en-IN" else "hi-IN")
      putExtra(RecognizerIntent.EXTRA_PROMPT, "NOVA sun rahi hai, boliye…")
  }
  startActivityForResult(i, 2026)
        } catch (_: Exception) {
  webView.evaluateJavascript("window.onNovaSpeechError && window.onNovaSpeechError()", null)
        }
    }
    @Deprecated("Deprecated in Android")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == 2026) {
  val spoken = if (resultCode == RESULT_OK) data?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)?.firstOrNull() else null
  val js = if (spoken.isNullOrBlank()) "window.onNovaSpeechError && window.onNovaSpeechError()" else "window.onNovaSpeechResult && window.onNovaSpeechResult(${JSONObject.quote(spoken)})"
  webView.evaluateJavascript(js, null)
        }
    }
    @Deprecated("Deprecated in Android")
    override fun onBackPressed() { if (::webView.isInitialized && webView.canGoBack()) webView.goBack() else super.onBackPressed() }
}
""", encoding="utf-8")
# Route speech through Android TextToSpeech; route speech input through Android recognizer.
old = "  if (!('speechSynthesis' in window)) return;\n  if (forceAuto && !state.autoSpeak) return;"
new = "  if (forceAuto && !state.autoSpeak) return;\n  if (window.NovaAndroidBridge) { if (isSpeaking) { window.NovaAndroidBridge.stopSpeaking(); } window.NovaAndroidBridge.speak(cleanSpeechText(text), lang === 'en' ? 'en' : 'hi'); isSpeaking = true; avatar.classList.add('speaking'); setTimeout(() => { isSpeaking = false; avatar.classList.remove('speaking'); }, Math.max(1800, String(text || '').length * 65)); return; }\n  if (!('speechSynthesis' in window)) return;"
assert old in s, "toggleSpeak entry not found"
# Define sanitizer before toggleSpeak and use it for native voice.
s = s.replace("function toggleSpeak(text, lang = 'hinglish'", "function cleanSpeechText(text) { return (text || '').replace(/https?:\\/\\/\\S+/g, '').replace(/[\\u{1F300}-\\u{1FAFF}]/gu, '').replace(/\\s+/g, ' ').trim(); }\n\nfunction toggleSpeak(text, lang = 'hinglish'", 1)
s = s.replace(old, new, 1)
s = s.replace("  if ('speechSynthesis' in window) speechSynthesis.cancel();", "  if (window.NovaAndroidBridge) window.NovaAndroidBridge.stopSpeaking();\n  if ('speechSynthesis' in window) speechSynthesis.cancel();", 1)
mic_start = "  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;\n  if (!SR || window.location.protocol === 'file:') {"
native_mic = """  if (window.NovaAndroidBridge) {
    isListening = true; micBtn.classList.add('listening');
    setAvatarState('listening', '🎙️', '🎙️ Sun rahi hoon…');
    hint.textContent = '🎙️ Boliye, NOVA sun rahi hai…';
    window.onNovaSpeechResult = transcript => { isListening = false; micBtn.classList.remove('listening'); input.value = transcript; send(); };
    window.onNovaSpeechError = () => { isListening = false; micBtn.classList.remove('listening'); hint.textContent = '⚠️ Voice input cancel hua ya available nahi hai.'; };
    window.NovaAndroidBridge.startVoiceInput(state.lang === 'en' ? 'en' : 'hi');
    return;
  }
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR || window.location.protocol === 'file:') {"""
assert mic_start in s, "mic handler marker not found"
s = s.replace(mic_start, native_mic, 1)
# Native app opens for action links (YouTube/song/search/maps).
s = s.replace("    link.href = actionUrl;\n    link.target = '_blank';", "    link.href = actionUrl;\n    link.target = '_blank';\n    if (window.NovaAndroidBridge) link.onclick = ev => { ev.preventDefault(); window.NovaAndroidBridge.openUrl(actionUrl); };", 1)
p.write_text(s, encoding="utf-8")
print("Patched native TTS, Android speech recognition, and external app/link launching")


# Native YouTube autoplay, flashlight/camera commands, and remove Android title bar.
from pathlib import Path as P
root = P("/tmp/nova-src/NOVA_v4.0_Complete")
hp = root / "app/src/main/assets/index.html"
s = hp.read_text(encoding="utf-8")
old = """  if (/\\b(flashlight|torch|flash light)\\b/i.test(lower)) {
    return { reply: '🔦 Browser se hardware torch directly control nahi hoti — Android CameraManager API ke saath Native APK mein chalegi.' };
  }"""
new = """  if (/\\b(flashlight|torch|flash light)\\b/i.test(lower)) {
    const off = /\\b(off|band|disable)\\b/i.test(lower);
    if (window.NovaAndroidBridge) {
      const ok = window.NovaAndroidBridge.toggleTorch(!off);
      return { reply: ok ? (off ? '🔦 Torch band kar di ✓' : '🔦 Torch on kar di ✓') : '⚠️ Torch unavailable hai; Camera permission allow karein.' };
    }
    return { reply: '⚠️ Torch ke liye NOVA Android app chahiye.' };
  }
  if (/\\b(open camera|camera kholo|camera khol|take photo|photo lo|selfie lo|camera)\\b/i.test(lower)) {
    if (window.NovaAndroidBridge) { window.NovaAndroidBridge.openCamera(); return { reply: '📷 Camera khol diya ✓' }; }
    return { reply: '⚠️ Camera ke liye NOVA Android app chahiye.' };
  }"""
if old in s: s = s.replace(old, new, 1)
elif "toggleTorch(!off)" not in s: raise SystemExit("Torch command marker missing")
needle = "    const watchUrl = " + chr(96) + "https://www.youtube.com/watch?v=" + chr(36) + "{picked.id}" + chr(96) + ";"
if needle in s and "playYouTube(watchUrl)" not in s:
    s = s.replace(needle, needle + "\n    if (window.NovaAndroidBridge) window.NovaAndroidBridge.playYouTube(watchUrl);", 1)
    s = s.replace("YouTube par kholne ke liye neeche button tap karein.", "YouTube par gaana play kar rahi hoon…", 1)
hp.write_text(s, encoding="utf-8")

bp = root / "app/src/main/java/com/nova/companion/NovaAndroidBridge.kt"
b = bp.read_text(encoding="utf-8")
marker = "    @JavascriptInterface fun openApp(appKey: String): Boolean {"
methods = '''    @JavascriptInterface
    fun playYouTube(url: String) {
        try {
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url)).setPackage("com.google.android.youtube")
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(intent)
        } catch (_: Exception) { openUrl(url) }
    }
    @JavascriptInterface
    fun toggleTorch(enabled: Boolean): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.M) return false
        return try {
            val manager = context.getSystemService(Context.CAMERA_SERVICE) as android.hardware.camera2.CameraManager
            val id = manager.cameraIdList.firstOrNull {
                manager.getCameraCharacteristics(it).get(android.hardware.camera2.CameraCharacteristics.FLASH_INFO_AVAILABLE) == true
            } ?: return false
            manager.setTorchMode(id, enabled)
            true
        } catch (_: SecurityException) {
            (context as? MainActivity)?.requestCameraPermission()
            false
        } catch (_: Exception) { false }
    }
    @JavascriptInterface
    fun openCamera() {
        try { context.startActivity(Intent(android.provider.MediaStore.ACTION_IMAGE_CAPTURE).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
        catch (_: Exception) { Toast.makeText(context, "Camera app nahi mili", Toast.LENGTH_SHORT).show() }
    }

'''
if "fun playYouTube(url: String)" not in b:
    if marker not in b: raise SystemExit("Bridge insertion marker missing")
    b = b.replace(marker, methods + marker, 1)
bp.write_text(b, encoding="utf-8")

ap = root / "app/src/main/java/com/nova/companion/MainActivity.kt"
a = ap.read_text(encoding="utf-8")
if "fun requestCameraPermission()" not in a:
    insert = '''    fun requestCameraPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED)
            ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.CAMERA), 303)
    }
'''
    marker = '    @Deprecated("Deprecated in Android")'
    if marker not in a: raise SystemExit("Activity insertion marker missing")
    a = a.replace(marker, insert + marker, 1)
ap.write_text(a, encoding="utf-8")

mp = root / "app/src/main/AndroidManifest.xml"
m = mp.read_text(encoding="utf-8")
if "android.permission.CAMERA" not in m:
    m = m.replace('    <uses-permission android:name="android.permission.RECORD_AUDIO" />', '    <uses-permission android:name="android.permission.RECORD_AUDIO" />\n    <uses-permission android:name="android.permission.CAMERA" />\n    <uses-feature android:name="android.hardware.camera" android:required="false" />')
m = m.replace('android:label="NOVA AI Companion"', 'android:label="NOVA"')
if 'android:theme="@android:style/Theme.Material.Light.NoActionBar"' not in m:
    m = m.replace('<application\n', '<application\n        android:theme="@android:style/Theme.Material.Light.NoActionBar"\n')
mp.write_text(m, encoding="utf-8")
print("Patched direct YouTube playback, torch/camera commands, and hidden app title bar")

# Fix app launch aliases and camera intent handling.
from pathlib import Path as P
import re as RE
root = P("/tmp/nova-src/NOVA_v4.0_Complete")
bp = root / "app/src/main/java/com/nova/companion/NovaAndroidBridge.kt"
k = bp.read_text(encoding="utf-8")
k = k.replace('"play store" to "com.android.vending"', '"play store" to "com.android.vending",\n        "free fire" to "com.dts.freefiremax",\n        "free fire max" to "com.dts.freefiremax",\n        "freefire" to "com.dts.freefiremax",\n        "freefire max" to "com.dts.freefiremax"')
old = '''    @JavascriptInterface fun openApp(appKey: String): Boolean {
        val pkg = packageMap[appKey.lowercase().trim()] ?: return false
        val i = context.packageManager.getLaunchIntentForPackage(pkg) ?: return false
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK); context.startActivity(i); return true
    }'''
new = '''    @JavascriptInterface fun openApp(appKey: String): Boolean {
        val pkg = packageMap[appKey.lowercase().trim()] ?: return false
        val i = context.packageManager.getLaunchIntentForPackage(pkg) ?: return false
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK); context.startActivity(i); return true
    }'''
if old in k: k = k.replace(old, new, 1)
pattern = r'''    @JavascriptInterface\s+fun openCamera\(\)\s*\{.*?\n    \}'''
camera = '''    @JavascriptInterface fun openCamera(): Boolean {
        val pm = context.packageManager
        for (action in listOf("android.media.action.STILL_IMAGE_CAMERA", "android.media.action.IMAGE_CAPTURE")) {
            try {
                val intent = Intent(action).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                if (intent.resolveActivity(pm) != null) {
                    context.startActivity(intent)
                    return true
                }
            } catch (_: Exception) {}
        }
        Toast.makeText(context, "Camera app installed/enabled nahi mil rahi", Toast.LENGTH_LONG).show()
        return false
    }'''
k, n = RE.subn(pattern, camera, k, count=1, flags=RE.S)
if n != 1: raise SystemExit("Could not replace native camera method")
bp.write_text(k, encoding="utf-8")
hp = root / "app/src/main/assets/index.html"
h = hp.read_text(encoding="utf-8")
h = h.replace("    { keys: ['playstore', 'play store'], name: 'Play Store', url: 'https://play.google.com/store' },", "    { keys: ['free fire max', 'freefire max', 'free fire', 'freefire'], name: 'Free Fire MAX', url: 'https://play.google.com/store/apps/details?id=com.dts.freefiremax' },\n    { keys: ['playstore', 'play store'], name: 'Play Store', url: 'https://play.google.com/store' },")
old_cam = "    if (window.NovaAndroidBridge) { window.NovaAndroidBridge.openCamera(); return { reply: '📷 Camera khol diya ✓' }; }\n    return { reply: '⚠️ Camera ke liye NOVA Android app chahiye.' };"
new_cam = "    if (window.NovaAndroidBridge && window.NovaAndroidBridge.openCamera()) return { reply: '📷 Camera open kar diya ✓' };\n    return { reply: '⚠️ Is phone par camera app launch nahi ho paayi. Default Camera app enabled hai ya nahi check karein.' };"
h = h.replace(old_cam, new_cam, 1)
hp.write_text(h, encoding="utf-8")
mp = root / "app/src/main/AndroidManifest.xml"
m = mp.read_text(encoding="utf-8")
if "<queries>" not in m:
    m = m.replace("    <application", '''    <queries>
        <package android:name="com.dts.freefiremax" />
        <package android:name="com.dts.freefireth" />
        <package android:name="com.google.android.youtube" />
        <package android:name="com.whatsapp" />
        <package android:name="com.instagram.android" />
        <package android:name="com.spotify.music" />
        <package android:name="com.google.android.apps.maps" />
        <intent><action android:name="android.media.action.STILL_IMAGE_CAMERA" /></intent>
        <intent><action android:name="android.media.action.IMAGE_CAPTURE" /></intent>
    </queries>
    <application''', 1)
mp.write_text(m, encoding="utf-8")
print("Fixed Free Fire MAX launch, package visibility, and Camera intent fallback")


# Dynamic all-app launching and native device controls.
from pathlib import Path as P
import re as RE
root=P("/tmp/nova-src/NOVA_v4.0_Complete")
bp=root/"app/src/main/java/com/nova/companion/NovaAndroidBridge.kt"
k=bp.read_text(encoding="utf-8")
# Remove earlier torch method before adding generalized bridge methods.
k=RE.sub(r'    @JavascriptInterface\s+fun toggleTorch\(enabled: Boolean\): Boolean \{.*?\n    \}', '', k, count=1, flags=RE.S)
for imp in ["import android.Manifest","import android.content.pm.PackageManager","import android.media.AudioManager","import android.hardware.camera2.CameraManager","import org.json.JSONArray","import org.json.JSONObject"]:
    if imp not in k: k=k.replace("import android.content.Context",imp+"\nimport android.content.Context",1)
old='''    @JavascriptInterface fun openApp(appKey: String): Boolean {
        val pkg = packageMap[appKey.lowercase().trim()] ?: return false
        val i = context.packageManager.getLaunchIntentForPackage(pkg) ?: return false
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK); context.startActivity(i); return true
    }'''
new='''    private fun norm(v:String)=v.lowercase().replace(Regex("[^a-z0-9]"),"")
    private fun launcherApps()=context.packageManager.queryIntentActivities(Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER),0)
    @JavascriptInterface fun getInstalledApps():String {
        val a=JSONArray()
        launcherApps().mapNotNull { r ->
            val n=r.loadLabel(context.packageManager)?.toString()?.trim()
            val p=r.activityInfo?.packageName
            if(!n.isNullOrBlank() && !p.isNullOrBlank()) JSONObject().put("name",n).put("package",p) else null
        }.distinctBy{it.optString("package")}.sortedBy{it.optString("name").lowercase()}.forEach{a.put(it)}
        return a.toString()
    }
    @JavascriptInterface fun openApp(appKey:String):Boolean {
        val q=norm(appKey); if(q.isBlank()) return false
        val pm=context.packageManager; val apps=launcherApps()
        val hit=apps.firstOrNull{norm(it.loadLabel(pm).toString())==q}
            ?: apps.firstOrNull{norm(it.loadLabel(pm).toString()).startsWith(q)}
            ?: apps.firstOrNull{q.length>=3 && norm(it.loadLabel(pm).toString()).contains(q)}
        val pkg=hit?.activityInfo?.packageName ?: packageMap[appKey.lowercase().trim()] ?: return false
        return try { val i=pm.getLaunchIntentForPackage(pkg) ?: return false; i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK); context.startActivity(i); true } catch(_:Exception){false}
    }
    @JavascriptInterface fun openCamera():Boolean {
        for(action in listOf("android.media.action.STILL_IMAGE_CAMERA","android.media.action.IMAGE_CAPTURE")) try {
            val i=Intent(action).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            if(i.resolveActivity(context.packageManager)!=null){context.startActivity(i);return true}
        } catch(_:Exception){}
        return false
    }
    @JavascriptInterface fun toggleTorch(on:Boolean):Boolean=try {
        if(Build.VERSION.SDK_INT<23)return false
        val cm=context.getSystemService(Context.CAMERA_SERVICE) as CameraManager
        val id=cm.cameraIdList.firstOrNull{cm.getCameraCharacteristics(it).get(android.hardware.camera2.CameraCharacteristics.FLASH_INFO_AVAILABLE)==true}?:return false
        cm.setTorchMode(id,on);true
    }catch(_:Exception){false}
    @JavascriptInterface fun adjustVolume(dir:String):Boolean=try {
        val am=context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
        val v=when(dir.lowercase()){"up"->AudioManager.ADJUST_RAISE;"down"->AudioManager.ADJUST_LOWER;"mute"->AudioManager.ADJUST_MUTE;"unmute"->AudioManager.ADJUST_UNMUTE;else->return false}
        am.adjustStreamVolume(AudioManager.STREAM_MUSIC,v,AudioManager.FLAG_SHOW_UI);true
    }catch(_:Exception){false}
    @JavascriptInterface fun openSystemPanel(name:String):Boolean=try {
        val action=when(name.lowercase()){
            "wifi"->if(Build.VERSION.SDK_INT>=29)Settings.Panel.ACTION_WIFI else Settings.ACTION_WIFI_SETTINGS
            "bluetooth"->if(Build.VERSION.SDK_INT>=29)Settings.Panel.ACTION_BLUETOOTH else Settings.ACTION_BLUETOOTH_SETTINGS
            "brightness"->Settings.ACTION_DISPLAY_SETTINGS
            "sound"->Settings.ACTION_SOUND_SETTINGS
            else->Settings.ACTION_SETTINGS
        }
        context.startActivity(Intent(action).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));true
    }catch(_:Exception){false}
    @JavascriptInterface fun requestBatteryOptimizationExemption(){
        if(Build.VERSION.SDK_INT>=23)try{
            val pm=context.getSystemService(Context.POWER_SERVICE) as android.os.PowerManager
            if(!pm.isIgnoringBatteryOptimizations(context.packageName))
                context.startActivity(Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,Uri.parse("package:"+context.packageName)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        }catch(_:Exception){try{context.startActivity(Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))}catch(_:Exception){}}
    }
'''
if old in k:k=k.replace(old,new,1)
elif "fun getInstalledApps()" not in k:raise SystemExit("openApp insertion point missing")
k=k.replace('''    @JavascriptInterface fun startWakeWordService() {
        val i = Intent(context, NovaWakeWordService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) context.startForegroundService(i) else context.startService(i)
    }''','''    @JavascriptInterface fun startWakeWordService():Boolean {
        if(Build.VERSION.SDK_INT>=23 && context.checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){(context as? MainActivity)?.requestNovaPermissions();return false}
        return try{val i=Intent(context,NovaWakeWordService::class.java);if(Build.VERSION.SDK_INT>=26)context.startForegroundService(i)else context.startService(i);true}catch(_:Exception){false}
    }''')
bp.write_text(k,encoding="utf-8")
mp=root/"app/src/main/AndroidManifest.xml"
m=mp.read_text(encoding="utf-8")
if "android.intent.category.LAUNCHER" not in m:m=m.replace("</queries>",'<intent><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/></intent></queries>',1)
if "REQUEST_IGNORE_BATTERY_OPTIMIZATIONS" not in m:m=m.replace('<uses-permission android:name="android.permission.WAKE_LOCK" />','<uses-permission android:name="android.permission.WAKE_LOCK" />\n    <uses-permission android:name="android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS" />')
mp.write_text(m,encoding="utf-8")
ap=root/"app/src/main/java/com/nova/companion/MainActivity.kt"
a=ap.read_text(encoding="utf-8")
if "fun requestNovaPermissions()" not in a:a=a.replace('    @Deprecated("Deprecated in Android")','''    fun requestNovaPermissions(){val p=mutableListOf(Manifest.permission.RECORD_AUDIO);if(android.os.Build.VERSION.SDK_INT>=33)p.add(Manifest.permission.POST_NOTIFICATIONS);ActivityCompat.requestPermissions(this,p.toTypedArray(),410)}
    override fun onNewIntent(intent:android.content.Intent){super.onNewIntent(intent);setIntent(intent);if(intent.getBooleanExtra("auto_listen",false))webView.postDelayed({webView.evaluateJavascript("document.getElementById('mic')?.click()",null)},700)}
    @Deprecated("Deprecated in Android")''',1)
ap.write_text(a,encoding="utf-8")
hp=root/"app/src/main/assets/index.html"
h=hp.read_text(encoding="utf-8")
marker="  return null;\n}\n\n/* English-to-Hindi Translation Helper"
dyn='''  const genericOpen=lower.match(/^(?:open|launch|start)\\\\s+(.+?)(?:\\\\s+app)?$|^(.+?)\\\\s+(?:kholo|open|chalao)$/i);
  if(genericOpen && window.NovaAndroidBridge){const name=(genericOpen[1]||genericOpen[2]||'').trim();if(name&&!/^(camera|torch|flashlight|wifi|wi-fi|bluetooth|settings|volume|sound|brightness)$/.test(name)){try{if(window.NovaAndroidBridge.openApp(name))return{reply:'✅ '+name+' open kar diya!'};}catch{}return{reply:'⚠️ '+name+' naam ka installed app nahi mila.'};}}
  if(/^(list apps|show apps|mere apps|installed apps)$/i.test(lower)&&window.NovaAndroidBridge){try{const apps=JSON.parse(window.NovaAndroidBridge.getInstalledApps());return{reply:'📱 Installed apps: '+apps.map(x=>x.name).join(', ')};}catch{}}
'''
if dyn.strip() not in h:
    if marker not in h:raise SystemExit("HTML app-command insertion marker missing")
    h=h.replace(marker,dyn+marker,1)
h=h.replace('''  if (/\\b(wifi|wi-fi|bluetooth|hotspot|airplane|brightness|volume|screenshot)\\b/i.test(lower)) {
    return { reply: '⚙️ Android Chrome security ke kaaran browser system toggles/screenshot nahi le sakta — Native Android Companion APK mein supported hoga.' };
  }''','''  if (/\\b(volume up|increase volume|awaaz badhao|volume badhao)\\b/i.test(lower)&&window.NovaAndroidBridge)return{reply:window.NovaAndroidBridge.adjustVolume('up')?'🔊 Volume badha diya ✓':'Volume unavailable'};
  if (/\\b(volume down|decrease volume|awaaz kam|volume kam)\\b/i.test(lower)&&window.NovaAndroidBridge)return{reply:window.NovaAndroidBridge.adjustVolume('down')?'🔉 Volume kam kar diya ✓':'Volume unavailable'};
  if (/\\b(wifi|wi-fi|bluetooth|hotspot|airplane|brightness|display settings|sound settings)\\b/i.test(lower)&&window.NovaAndroidBridge){const p=/bluetooth/i.test(lower)?'bluetooth':/wifi|wi-fi|hotspot|airplane/i.test(lower)?'wifi':/sound/i.test(lower)?'sound':'brightness';return{reply:window.NovaAndroidBridge.openSystemPanel(p)?'⚙️ Android control panel khol diya. Yahan se change karein.':'System panel unavailable'};}
  if (/\\b(screenshot|screen shot)\\b/i.test(lower))return{reply:'📸 Silent screenshot Android security se restricted hai; phone ka screenshot gesture use karein.'};''',1)
wake='''<script>(function(){if(document.getElementById('novaWakeToggle'))return;const b=document.createElement('button');b.id='novaWakeToggle';b.textContent='🌙 Enable Hey NOVA';b.style.cssText='position:fixed;top:72px;right:12px;z-index:99999;border:1px solid #b66cff;border-radius:24px;padding:9px 14px;background:#21123d;color:white;font:600 13px system-ui';let active=false;b.onclick=function(){if(!window.NovaAndroidBridge)return;if(!active){const ok=window.NovaAndroidBridge.startWakeWordService();if(ok){active=true;b.textContent='🌙 Hey NOVA: ON';window.NovaAndroidBridge.requestBatteryOptimizationExemption();}else b.textContent='Allow microphone permission, then tap';}else{window.NovaAndroidBridge.stopWakeWordService();active=false;b.textContent='🌙 Enable Hey NOVA';}};document.body.appendChild(b);})();</script>'''
if "novaWakeToggle" not in h:h=h.replace("</body>",wake+"</body>",1)
hp.write_text(h,encoding="utf-8")
print("NOVA v5 dynamic apps + wake-word controls patched")
