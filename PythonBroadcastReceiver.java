package org.kivy.android;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.util.Log;
import androidx.core.app.NotificationCompat;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import java.io.File;

public class PythonBroadcastReceiver extends BroadcastReceiver {
    
    private static final String TAG = "TaskControlReminder";

    @Override
    public void onReceive(Context context, Intent intent) {
        Log.d(TAG, "onReceive called, intent=" + intent);
        int task_id = intent.getIntExtra("task_id", 0);
        String title = intent.getStringExtra("title");
        String type = intent.getStringExtra("type");
        
        Log.d(TAG, "DEBUG: Raw intent extras: title=" + title + ", task_id=" + task_id);
        
        if (title == null && task_id > 0) {
            try {
                File dbFile = new File(context.getFilesDir(), "app/tasks.db");
                Log.d(TAG, "DEBUG: DB file path=" + dbFile.getPath() + ", exists=" + dbFile.exists());
                
                if (dbFile.exists()) {
                    SQLiteDatabase db = SQLiteDatabase.openDatabase(dbFile.getPath(), null, SQLiteDatabase.OPEN_READONLY);
                    Cursor cursor = db.query("tasks", new String[]{"title"}, "id = ?", new String[]{String.valueOf(task_id)}, null, null, null);
                    Log.d(TAG, "DEBUG: Cursor count=" + cursor.getCount());
                    
                    if (cursor.moveToFirst()) {
                        title = cursor.getString(0);
                        Log.d(TAG, "DEBUG: Title found in DB: " + title);
                    } else {
                        Log.d(TAG, "DEBUG: No task found with id=" + task_id);
                    }
                    cursor.close();
                    db.close();
                } else {
                    Log.e(TAG, "DEBUG: DB file not found at " + dbFile.getPath());
                }
            } catch (Exception e) {
                Log.e(TAG, "Error fetching title from DB: " + e.getMessage(), e);
            }
        }
        if (title == null) title = "Задача";
        
        String message = "";
        if ("before".equals(type)) {
            message = "Через час начнется: " + title;
        } else if ("exact".equals(type)) {
            message = "Время пришло: " + title;
        } else {
            message = "Началось: " + title;
        }
        
        Log.d(TAG, "Notification title set to: " + title);
        Log.d(TAG, "Notification message set to: " + message);

        Intent notificationIntent = new Intent(context, PythonActivity.class);
        notificationIntent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        notificationIntent.putExtra("open_task_id", task_id);
        
        PendingIntent pendingIntent;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            pendingIntent = PendingIntent.getActivity(
                context, 
                task_id, 
                notificationIntent, 
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
            );
        } else {
            pendingIntent = PendingIntent.getActivity(
                context, 
                task_id, 
                notificationIntent, 
                PendingIntent.FLAG_UPDATE_CURRENT
            );
        }
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationManager notificationManager = 
                (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
            
            NotificationChannel channel = new NotificationChannel(
                "task_reminder_channel",
                "Напоминания о задачах",
                NotificationManager.IMPORTANCE_HIGH
            );
            
            if (notificationManager != null) {
                notificationManager.createNotificationChannel(channel);
            }
        }
        
        NotificationCompat.Builder builder = new NotificationCompat.Builder(context, "task_reminder_channel")
            .setContentTitle(title)
            .setContentText(message)
            .setSmallIcon(context.getApplicationInfo().icon)
            .setAutoCancel(true)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setDefaults(NotificationCompat.DEFAULT_ALL)
            .setContentIntent(pendingIntent);
        
        NotificationManager notificationManager = 
            (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (notificationManager != null) {
            notificationManager.notify(task_id, builder.build());
            Log.d(TAG, "notificationManager.notify called successfully.");
        }
    }
}
