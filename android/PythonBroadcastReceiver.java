package org.kivy.android;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import androidx.core.app.NotificationCompat;

public class PythonBroadcastReceiver extends BroadcastReceiver {
    
    @Override
    public void onReceive(Context context, Intent intent) {
        String title = intent.getStringExtra("title");
        String type = intent.getStringExtra("type");
        int task_id = intent.getIntExtra("task_id", 0);
        
        String message = "";
        if ("before".equals(type)) {
            message = "Через час начнется: " + title;
        } else {
            message = "Началось: " + title;
        }
        
        // Создаем интент для открытия приложения при клике
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
        
        // Создаем канал уведомлений (если еще не создан)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationManager notificationManager = 
                (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
            NotificationChannel channel = new NotificationChannel(
                "task_reminder_channel",
                "Напоминания о задачах",
                NotificationManager.IMPORTANCE_DEFAULT
            );
            channel.setDescription("Уведомления о предстоящих задачах");
            notificationManager.createNotificationChannel(channel);
        }
        
        // Создаем уведомление
        NotificationCompat.Builder builder = new NotificationCompat.Builder(context, "task_reminder_channel")
            .setContentTitle("Напоминание о задаче")
            .setContentText(message)
            .setSmallIcon(context.getApplicationInfo().icon)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent);
        
        Notification notification = builder.build();
        
        NotificationManager notificationManager = 
            (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        notificationManager.notify(task_id, notification);
    }
}
