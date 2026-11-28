from pathlib import Path
ROOT=Path("/tmp/nova-src/NOVA_v4.0_Complete"); JAVA=ROOT/"app/src/main/java/com/nova/companion"; HTML=ROOT/"app/src/main/assets/index.html"; MANIFEST=ROOT/"app/src/main/AndroidManifest.xml"
from shutil import copyfile
icon_source=Path("app/src/main/res/drawable-nodpi/nova_launcher.png")
if not icon_source.exists(): raise SystemExit("NOVA launcher icon asset missing from repository")
icon_target=ROOT/"app/src/main/res/drawable-nodpi/nova_launcher.png"
icon_target.parent.mkdir(parents=True,exist_ok=True)
copyfile(icon_source,icon_target)
s=HTML.read_text(encoding="utf-8"); marker="state = { ...state, ...JSON.parse(localStorage.getItem(settingsKey) || '{}') };"
if "nova-ai-brain.hy1009568.workers.dev" not in s:s=s.replace(marker,marker+"\nif (!state.backendUrl) state.backendUrl='https://nova-ai-brain.hy1009568.workers.dev';",1)
bridge=r'''package com.nova.companion
import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.provider.Settings
import android.speech.tts.TextToSpeech
import android.webkit.JavascriptInterface
import android.widget.Toast
import android.hardware.camera2.CameraManager
import java.util.Locale
class NovaAndroidBridge(private val context:Context):TextToSpeech.OnInitListener {
 private val tts=TextToSpeech(context,this); @Volatile private var ready=false
 private val aliases=mapOf("youtube" to "com.google.android.youtube","yt" to "com.google.android.youtube","whatsapp" to "com.whatsapp","instagram" to "com.instagram.android","spotify" to "com.spotify.music","google maps" to "com.google.android.apps.maps","gmail" to "com.google.android.gm","telegram" to "org.telegram.messenger","amazon" to "in.amazon.mShop.android.shopping","flipkart" to "com.flipkart.android","play store" to "com.android.vending","free fire" to "com.dts.freefiremax","free fire max" to "com.dts.freefiremax","freefire" to "com.dts.freefiremax")
 override fun onInit(status:Int){ready=status==TextToSpeech.SUCCESS}
 @JavascriptInterface fun speak(text:String,language:String){if(!ready)return;tts.language=if(language=="en")Locale("en","IN") else Locale("hi","IN");tts.setSpeechRate(.94f);tts.setPitch(1.12f);if(Build.VERSION.SDK_INT>=21)tts.speak(text,TextToSpeech.QUEUE_FLUSH,null,"nova_reply") else @Suppress("DEPRECATION") tts.speak(text,TextToSpeech.QUEUE_FLUSH,null)}
 @JavascriptInterface fun stopSpeaking(){if(ready)tts.stop()}
 @JavascriptInterface fun startVoiceInput(language:String){(context as? MainActivity)?.startNovaVoiceRecognition(language)}
 @JavascriptInterface fun openUrl(url:String){try{context.startActivity(Intent(Intent.ACTION_VIEW,Uri.parse(url)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))}catch(_:Exception){Toast.makeText(context,"App/link nahi khul paya",Toast.LENGTH_SHORT).show()}}
 private fun norm(v:String)=v.lowercase(Locale.ROOT).replace(Regex("[^a-z0-9]+")," ").trim().replace(Regex("\\s+")," ")
 @JavascriptInterface fun openApp(appName:String):Boolean{
  val key=norm(appName);if(key.isBlank())return false
  if(key=="settings"||key=="phone settings"||key=="system settings")return try{context.startActivity(Intent(Settings.ACTION_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));true}catch(_:Exception){false}
  val pm=context.packageManager
  aliases[key]?.let{pkg->try{val i=pm.getLaunchIntentForPackage(pkg);if(i!=null){i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);context.startActivity(i);return true}}catch(_:Exception){}}
  return try{val apps=pm.getInstalledApplications(PackageManager.GET_META_DATA).mapNotNull{a->val i=pm.getLaunchIntentForPackage(a.packageName)?:return@mapNotNull null;Triple(norm(pm.getApplicationLabel(a).toString()),a.packageName,i)}
   val found=apps.firstOrNull{it.first==key||norm(it.second)==key}?:apps.filter{it.first.contains(key)}.maxByOrNull{it.first.length}?:return false
   found.third.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);context.startActivity(found.third);true
  }catch(_:Exception){false}
 }
 @JavascriptInterface fun openCamera():Boolean{for(action in listOf("android.media.action.STILL_IMAGE_CAMERA","android.media.action.IMAGE_CAPTURE"))try{val i=Intent(action).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);if(i.resolveActivity(context.packageManager)!=null){context.startActivity(i);return true}}catch(_:Exception){};return false}
 @JavascriptInterface fun toggleTorch(on:Boolean):Boolean{if(Build.VERSION.SDK_INT<23)return false;if(context.checkSelfPermission(Manifest.permission.CAMERA)!=PackageManager.PERMISSION_GRANTED){(context as? MainActivity)?.requestCameraPermission();return false};return try{val m=context.getSystemService(Context.CAMERA_SERVICE) as CameraManager;val id=m.cameraIdList.firstOrNull{m.getCameraCharacteristics(it).get(android.hardware.camera2.CameraCharacteristics.FLASH_INFO_AVAILABLE)==true}?:return false;m.setTorchMode(id,on);true}catch(_:Exception){false}}
 @JavascriptInterface fun startWakeWordService():Boolean{if(context.checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){(context as? MainActivity)?.requestMicPermission();return false};return try{val i=Intent(context,NovaWakeWordService::class.java);if(Build.VERSION.SDK_INT>=26)context.startForegroundService(i)else context.startService(i);true}catch(_:Exception){false}}
 @JavascriptInterface fun stopWakeWordService(){context.stopService(Intent(context,NovaWakeWordService::class.java))}
 @JavascriptInterface fun requestBatteryOptimizationExemption(){if(Build.VERSION.SDK_INT>=23)try{val pm=context.getSystemService(Context.POWER_SERVICE) as android.os.PowerManager;if(!pm.isIgnoringBatteryOptimizations(context.packageName))context.startActivity(Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,Uri.parse("package:"+context.packageName)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))}catch(_:Exception){try{context.startActivity(Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))}catch(_:Exception){}}}
 @JavascriptInterface fun toggleFloatingBubble(){if(!Settings.canDrawOverlays(context)){context.startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,Uri.parse("package:"+context.packageName)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));return};context.startService(Intent(context,NovaFloatingOverlayService::class.java))}
}
'''
(JAVA/"NovaAndroidBridge.kt").write_text(bridge,encoding="utf-8")
activity=r'''package com.nova.companion
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
class MainActivity:ComponentActivity(){
 private lateinit var webView:WebView
 override fun onCreate(savedInstanceState:Bundle?){super.onCreate(savedInstanceState);if(ContextCompat.checkSelfPermission(this,Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED)requestMicPermission()
  webView=WebView(this);webView.settings.javaScriptEnabled=true;webView.settings.domStorageEnabled=true;webView.settings.mediaPlaybackRequiresUserGesture=false;webView.settings.allowFileAccess=true
  webView.webChromeClient=object:WebChromeClient(){override fun onPermissionRequest(r:PermissionRequest){runOnUiThread{r.grant(r.resources)}}}
  webView.webViewClient=object:WebViewClient(){override fun shouldOverrideUrlLoading(v:WebView?,r:WebResourceRequest?):Boolean{val u=r?.url?.toString()?:return false;if(u.startsWith("file:///android_asset/"))return false;try{startActivity(Intent(Intent.ACTION_VIEW,android.net.Uri.parse(u)))}catch(_:Exception){};return true}}
  webView.addJavascriptInterface(NovaAndroidBridge(this),"NovaAndroidBridge");setContentView(webView);webView.loadUrl("file:///android_asset/index.html");handleWake(intent)
 }
 fun requestMicPermission(){ActivityCompat.requestPermissions(this,arrayOf(Manifest.permission.RECORD_AUDIO,Manifest.permission.POST_NOTIFICATIONS),100)}
 fun requestCameraPermission(){ActivityCompat.requestPermissions(this,arrayOf(Manifest.permission.CAMERA),303)}
 override fun onNewIntent(i:Intent){super.onNewIntent(i);setIntent(i);handleWake(i)}
 private fun handleWake(i:Intent?){if(i?.getBooleanExtra("auto_listen",false)!=true)return;val c=i.getStringExtra("wake_command").orEmpty();webView.postDelayed({if(c.isNotBlank())webView.evaluateJavascript("window.onNovaWakeCommand && window.onNovaWakeCommand("+JSONObject.quote(c)+")",null)else startNovaVoiceRecognition("hi")},1000)}
 fun startNovaVoiceRecognition(language:String){if(ContextCompat.checkSelfPermission(this,Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){requestMicPermission();return};try{val i=Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply{putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);putExtra(RecognizerIntent.EXTRA_LANGUAGE,if(language=="en")"en-IN" else "hi-IN");putExtra(RecognizerIntent.EXTRA_PROMPT,"NOVA sun rahi hai, boliye…")};startActivityForResult(i,2026)}catch(_:Exception){webView.evaluateJavascript("window.onNovaSpeechError && window.onNovaSpeechError()",null)}}
 @Deprecated("Deprecated in Android") override fun onActivityResult(req:Int,res:Int,data:Intent?){super.onActivityResult(req,res,data);if(req==2026){val said=if(res==RESULT_OK)data?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)?.firstOrNull() else null;val js=if(said.isNullOrBlank())"window.onNovaSpeechError && window.onNovaSpeechError()" else "window.onNovaSpeechResult && window.onNovaSpeechResult("+JSONObject.quote(said)+")";webView.evaluateJavascript(js,null)}}
 @Deprecated("Deprecated in Android") override fun onBackPressed(){if(::webView.isInitialized&&webView.canGoBack())webView.goBack()else super.onBackPressed()}
}
'''
(JAVA/"MainActivity.kt").write_text(activity,encoding="utf-8")
wake=r'''package com.nova.companion
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.Bundle
import android.os.IBinder
import android.os.PowerManager
import android.os.Handler
import android.os.Looper
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import androidx.core.app.NotificationCompat
class NovaWakeWordService:Service(){
 private var rec:SpeechRecognizer?=null;private val h=Handler(Looper.getMainLooper());private var listening=false;private var active=true;private var lock:PowerManager.WakeLock?=null
 override fun onCreate(){super.onCreate();getSystemService(NotificationManager::class.java).createNotificationChannel(NotificationChannel("nova_wake_channel","NOVA Wake Word",NotificationManager.IMPORTANCE_LOW))
  val pi=PendingIntent.getActivity(this,1,Intent(this,MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP),PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
  val n=NotificationCompat.Builder(this,"nova_wake_channel").setContentTitle("NOVA is listening").setContentText("Screen-off Hey NOVA is active").setSmallIcon(android.R.drawable.ic_btn_speak_now).setContentIntent(pi).setOngoing(true).build()
  if(Build.VERSION.SDK_INT>=29)startForeground(1001,n,ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE)else startForeground(1001,n)
  try{lock=(getSystemService(POWER_SERVICE) as PowerManager).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK,"NOVA:WakeWord").also{it.acquire()}}catch(_:Exception){}
  getSharedPreferences("nova",MODE_PRIVATE).edit().putBoolean("wake_running",true).apply();if(SpeechRecognizer.isRecognitionAvailable(this))initRecognizer();listen()
 }
 private fun initRecognizer(){rec=SpeechRecognizer.createSpeechRecognizer(this).apply{setRecognitionListener(object:RecognitionListener{
  override fun onReadyForSpeech(p:Bundle?){listening=true};override fun onBeginningOfSpeech(){};override fun onRmsChanged(v:Float){};override fun onBufferReceived(b:ByteArray?){};override fun onEndOfSpeech(){listening=false}
  override fun onError(e:Int){listening=false;restart(if(e==SpeechRecognizer.ERROR_RECOGNIZER_BUSY)1600 else 900)}
  override fun onResults(b:Bundle?){listening=false;val heard=b?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull()?.lowercase().orEmpty();val match=Regex("(?:hey|hi|hello)\\s+nova").find(heard);if(match!=null)wake(heard.substring(match.range.last+1).trim(' ', ',', '.', '!', '?'));restart(500)}
  override fun onPartialResults(b:Bundle?){};override fun onEvent(e:Int,b:Bundle?){}
 })}}
 private fun listen(){if(!active||listening)return;val i=Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply{putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);putExtra(RecognizerIntent.EXTRA_LANGUAGE,"en-IN");putExtra(RecognizerIntent.EXTRA_MAX_RESULTS,1)};try{rec?.startListening(i)}catch(_:Exception){restart(1200)}}
 private fun restart(ms:Long){if(active)h.postDelayed({listen()},ms)}
 private fun wake(command:String){val i=Intent(this,MainActivity::class.java).apply{addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP);putExtra("auto_listen",true);putExtra("wake_command",command)};try{startActivity(i)}catch(_:Exception){val pi=PendingIntent.getActivity(this,2,i,PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE);(getSystemService(NOTIFICATION_SERVICE) as NotificationManager).notify(1002,NotificationCompat.Builder(this,"nova_wake_channel").setSmallIcon(android.R.drawable.ic_btn_speak_now).setContentTitle("Hey NOVA detected").setContentText("Tap to continue").setContentIntent(pi).setAutoCancel(true).build())}}
 override fun onDestroy(){active=false;h.removeCallbacksAndMessages(null);rec?.destroy();try{if(lock?.isHeld==true)lock?.release()}catch(_:Exception){};getSharedPreferences("nova",MODE_PRIVATE).edit().putBoolean("wake_running",false).apply();super.onDestroy()}
 override fun onBind(i:Intent?):IBinder?=null
}
'''
(JAVA/"NovaWakeWordService.kt").write_text(wake,encoding="utf-8")
m=MANIFEST.read_text(encoding="utf-8")
for perm in ['android.permission.QUERY_ALL_PACKAGES','android.permission.CAMERA','android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS']:
 if perm not in m:m=m.replace('    <uses-permission android:name="android.permission.INTERNET" />','    <uses-permission android:name="android.permission.INTERNET" />\n    <uses-permission android:name="'+perm+'" />',1)
m=m.replace('android:label="NOVA AI Companion"','android:label="NOVA"')
if 'android:icon="@drawable/nova_launcher"' not in m:m=m.replace('<application\n','<application\n        android:icon="@drawable/nova_launcher"\n        android:theme="@android:style/Theme.Material.Light.NoActionBar"\n',1)
MANIFEST.write_text(m,encoding="utf-8")
old="""  if (/\\b(flashlight|torch|flash light)\\b/i.test(lower)) {
    return { reply: '🔦 Browser se hardware torch directly control nahi hoti — Android CameraManager API ke saath Native APK mein chalegi.' };
  }"""
new="""  if (/\\b(flashlight|torch|flash light)\\b/i.test(lower)) {
    const off=/\\b(off|band|disable)\\b/i.test(lower),ok=window.NovaAndroidBridge?.toggleTorch(!off);
    return {reply:ok?(off?'🔦 Torch band kar di ✓':'🔦 Torch on kar di ✓'):'⚠️ Camera permission allow karein, phir torch command dobara boliye.'};
  }
  if (/\\b(open camera|camera kholo|camera khol|take photo|photo lo|selfie lo|camera)\\b/i.test(lower)) {
    const ok=window.NovaAndroidBridge?.openCamera();return {reply:ok?'📷 Camera open kar diya ✓':'⚠️ Default Camera app launch nahi ho paayi.'};
  }"""
if old in s:s=s.replace(old,new,1)
needle="    const watchUrl = "+chr(96)+"https://www.youtube.com/watch?v="+chr(36)+"{picked.id}"+chr(96)+";"
if needle in s and "openUrl(watchUrl)" not in s:s=s.replace(needle,needle+"\n    if (window.NovaAndroidBridge) window.NovaAndroidBridge.openUrl(watchUrl);",1)
anchor="  return null;\n}\n\n/* English-to-Hindi Translation Helper"
generic=r'''  // Launch any installed app by its visible Android app name.
  const genericMatch=lower.match(/^(?:open|launch|start|khol|kholo|chalao)\s+(.+?)$|^(.+?)\s+(?:kholo|open|chalao)$/i);
  if(genericMatch&&window.NovaAndroidBridge){const appName=(genericMatch[1]||genericMatch[2]||'').trim();if(appName&&!/^(song|music|random song|camera|torch|flashlight)$/i.test(appName)){if(window.NovaAndroidBridge.openApp(appName))return{reply:'✅ '+appName+' open kar diya!'};return{reply:'⚠️ "'+appName+'" naam ka installed app nahi mila.'};}}
'''
if "Launch any installed app" not in s:s=s.replace(anchor,generic+anchor,1)
btn='<button class="mini-btn" style="width:100%;" id="testVoiceBtn">🔊 Test NOVA Voice</button>'
if 'id="heyNovaBtn"' not in s:s=s.replace(btn,btn+'''
      <button class="mini-btn" style="width:100%;margin-top:8px;" id="heyNovaBtn">🌙 Enable Hey NOVA (Screen Off)</button>
      <div style="font-size:11px;color:var(--muted);margin-top:5px;">Enable while NOVA is open. Persistent mic notification rahegi; battery exemption allow karein.</div>
      <button class="mini-btn" style="width:100%;margin-top:6px;" id="stopHeyNovaBtn">⏹ Stop Hey NOVA Listening</button>''',1)
events="""document.getElementById('heyNovaBtn')?.addEventListener('click',()=>{const ok=window.NovaAndroidBridge?.startWakeWordService();if(ok){window.NovaAndroidBridge.requestBatteryOptimizationExemption();document.getElementById('heyNovaBtn').textContent='🟢 Hey NOVA is Active';hint.textContent='🌙 Hey NOVA active — screen off par bhi sunegi (battery use hoga).';}else hint.textContent='⚠️ Microphone permission allow karein, phir dobara Enable dabayein.';});
document.getElementById('stopHeyNovaBtn')?.addEventListener('click',()=>{window.NovaAndroidBridge?.stopWakeWordService();document.getElementById('heyNovaBtn').textContent='🌙 Enable Hey NOVA (Screen Off)';hint.textContent='Hey NOVA listening stopped.';});
window.onNovaWakeCommand=command=>{if(command){input.value=command;send();}else micBtn.click();};
"""
if "window.onNovaWakeCommand=command" not in s:s=s.replace("document.getElementById('testVoiceBtn').onclick = () => {",events+"document.getElementById('testVoiceBtn').onclick = () => {",1)
HTML.write_text(s,encoding="utf-8")
print("NOVA patch complete")

# Rebuild verification: dynamic app discovery and Hey NOVA service integration.

# Add remaining Android controls that are available without privileged/root access.
bp=JAVA/"NovaAndroidBridge.kt"
k=bp.read_text(encoding="utf-8")
if "fun adjustVolume(" not in k:
 k=k.replace("import android.hardware.camera2.CameraManager","import android.hardware.camera2.CameraManager\nimport android.media.AudioManager")
 methods=''' @JavascriptInterface fun adjustVolume(direction:String):Boolean {
  return try { val am=context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
   val a=when(direction.lowercase()){"up"->AudioManager.ADJUST_RAISE;"down"->AudioManager.ADJUST_LOWER;"mute"->AudioManager.ADJUST_MUTE;"unmute"->AudioManager.ADJUST_UNMUTE;else->return false}
   am.adjustStreamVolume(AudioManager.STREAM_MUSIC,a,AudioManager.FLAG_SHOW_UI);true
  } catch(_:Exception){false}
 }
 @JavascriptInterface fun openSystemPanel(panel:String):Boolean {
  val action=when(panel.lowercase()){"wifi"->if(Build.VERSION.SDK_INT>=29)Settings.Panel.ACTION_WIFI else Settings.ACTION_WIFI_SETTINGS;"bluetooth"->Settings.ACTION_BLUETOOTH_SETTINGS;"brightness"->Settings.ACTION_DISPLAY_SETTINGS;"sound"->Settings.ACTION_SOUND_SETTINGS;else->Settings.ACTION_SETTINGS}
  return try{context.startActivity(Intent(action).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));true}catch(_:Exception){false}
 }
'''
 k=k.replace(" @JavascriptInterface fun startWakeWordService()",methods+" @JavascriptInterface fun startWakeWordService()",1)
bp.write_text(k,encoding="utf-8")
s=HTML.read_text(encoding="utf-8")
old='''  if (/\\b(wifi|wi-fi|bluetooth|hotspot|airplane|brightness|volume|screenshot)\\b/i.test(lower)) {
    return { reply: '⚙️ Android Chrome security ke kaaran browser system toggles/screenshot nahi le sakta — Native Android Companion APK mein supported hoga.' };
  }'''
new='''  if (/\\b(volume up|increase volume|awaaz badhao|volume badhao)\\b/i.test(lower) && window.NovaAndroidBridge) return {reply:window.NovaAndroidBridge.adjustVolume('up')?'🔊 Volume badha diya ✓':'Volume unavailable'};
  if (/\\b(volume down|decrease volume|awaaz kam|volume kam)\\b/i.test(lower) && window.NovaAndroidBridge) return {reply:window.NovaAndroidBridge.adjustVolume('down')?'🔉 Volume kam kar diya ✓':'Volume unavailable'};
  if (/\\b(mute|unmute)\\b/i.test(lower) && window.NovaAndroidBridge) {const d=/unmute/i.test(lower)?'unmute':'mute';return {reply:window.NovaAndroidBridge.adjustVolume(d)?'🔊 Volume updated':'Volume unavailable'};}
  if (/\\b(wifi|wi-fi|bluetooth|hotspot|airplane|brightness|display settings|sound settings)\\b/i.test(lower) && window.NovaAndroidBridge) {
    const p=/bluetooth/i.test(lower)?'bluetooth':/wifi|wi-fi|hotspot|airplane/i.test(lower)?'wifi':/sound/i.test(lower)?'sound':'brightness';
    return {reply:window.NovaAndroidBridge.openSystemPanel(p)?'⚙️ Android control panel khol diya. Yahan se setting change karein.':'System panel nahi khul paya.'};
  }
  if (/\\b(screenshot|screen shot)\\b/i.test(lower)) return {reply:'📸 Android security silent screenshot restrict karti hai; phone ka screenshot gesture use karein.'};'''
if old in s:s=s.replace(old,new,1)
HTML.write_text(s,encoding="utf-8")
print("Added volume controls and Android settings panels")
