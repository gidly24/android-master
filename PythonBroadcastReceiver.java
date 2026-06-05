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

public class PythonBroadcastReceiver extends BroadcastReceiver {
    
    private static final String TAG = "TaskControlReminder";

    @Override
    public void onReceive(Context context, Intent intent) {
        Log.d(TAG, "onReceive called, intent=" + intent);
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import java.io.File;

// ... inside onReceive ...
        int task_id = intent.getIntExtra("task_id", 0);
        String title = intent.getStringExtra("title");
        
        if (title == null && task_id > 0) {
            try {
                File dbFile = new File(context.getFilesDir(), "app/tasks.db");
                SQLiteDatabase db = SQLiteDatabase.openDatabase(dbFile.getPath(), null, SQLiteDatabase.OPEN_READONLY);
                Cursor cursor = db.query("tasks", new String[]{"title"}, "id = ?", new String[]{String.valueOf(task_id)}, null, null, null);
                if (cursor.moveToFirst()) {
                    title = cursor.getString(0);
                }
                cursor.close();
                db.close();
            } catch (Exception e) {
                Log.e(TAG, "Error fetching title from DB: " + e.getMessage());
            }
        }
        if (title == null) title = "Задача";
        
        if ("before".equals(type)) {
            message = "Через час начнется: " + title;
        } else if ("exact".equals(type)) {
            message = "Время пришло: " + title;
        } else {
            message = "Началось: " + title;
        }
        
        Log.d(TAG, "Notification title set to: " + title);
        Log.d(TAG, "Notification message set to: " + message);

        // ... (rest of the code unchanged)
        
        // Создаем уведомление
        NotificationCompat.Builder builder = new NotificationCompat.Builder(context, "task_reminder_channel")
            .setContentTitle(title)
            .setContentText(message)
            .setSmallIcon(context.getApplicationInfo().icon)
            .setAutoCancel(true)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setDefaults(NotificationCompat.DEFAULT_ALL)
            .setContentIntent(pendingIntent);
        
        Notification notification = builder.build();
        
        // Log notification build status
        if (notification != null) {
            Log.d(TAG, "Notification built successfully.");
        } else {
            Log.e(TAG, "Notification build failed.");
            return;
        }

        NotificationManager notificationManager = 
            (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        
        // Log if NotificationManager is null again before notifying
        if (notificationManager == null) {
            Log.e(TAG, "NotificationManager is null before notify call!");
            return;
        }

        try {
            // Log before calling notify
            Log.d(TAG, "Calling notificationManager.notify for task_id: " + task_id);
            notificationManager.notify(task_id, notification);
            Log.d(TAG, "notificationManager.notify called successfully.");
        } catch (Exception e) {
            Log.e(TAG, "Exception during notificationManager.notify: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
