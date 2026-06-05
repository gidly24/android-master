package org.kivy.android;

import android.app.NotificationChannel;
import android.app.Notification;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.util.Log;

public class PythonBroadcastReceiver extends BroadcastReceiver {
    private static final String TAG = "TaskControlReminder";
    private static final String CHANNEL_ID = "task_reminder_channel";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null) {
            return;
        }

        int taskId = intent.getIntExtra("task_id", 0);
        String title = intent.getStringExtra("title");
        if (title == null || title.length() == 0) {
            title = intent.getStringExtra("task_title");
        }
        if (title == null || title.length() == 0) {
            title = "Задача";
        }

        String message = "Время пришло: " + title;
        Log.d(TAG, "Alarm received for task_id=" + taskId + ", title=" + title);

        NotificationManager notificationManager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (notificationManager == null) {
            Log.e(TAG, "NotificationManager is null");
            startApp(context, taskId);
            return;
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID,
                    "Напоминания о задачах",
                    NotificationManager.IMPORTANCE_HIGH
            );
            channel.setDescription("Уведомления о предстоящих задачах");
            notificationManager.createNotificationChannel(channel);
        }

        PendingIntent contentIntent = PendingIntent.getActivity(
                context,
                taskId,
                buildLaunchIntent(context, taskId),
                pendingIntentFlags()
        );

        Notification.Builder builder;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            builder = new Notification.Builder(context, CHANNEL_ID);
        } else {
            builder = new Notification.Builder(context);
        }

        builder.setContentTitle("Напоминание о задаче")
                .setContentText(message)
                .setSmallIcon(context.getApplicationInfo().icon)
                .setAutoCancel(true)
                .setContentIntent(contentIntent)
                .setDefaults(Notification.DEFAULT_ALL)
                .setPriority(Notification.PRIORITY_HIGH);

        notificationManager.notify(taskId, builder.build());
        startApp(context, taskId);
    }

    private Intent buildLaunchIntent(Context context, int taskId) {
        Intent launchIntent = new Intent(context, PythonActivity.class);
        launchIntent.setFlags(
                Intent.FLAG_ACTIVITY_NEW_TASK |
                Intent.FLAG_ACTIVITY_CLEAR_TOP |
                Intent.FLAG_ACTIVITY_SINGLE_TOP
        );
        launchIntent.putExtra("open_task_id", taskId);
        return launchIntent;
    }

    private int pendingIntentFlags() {
        int flags = PendingIntent.FLAG_UPDATE_CURRENT;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            flags |= PendingIntent.FLAG_IMMUTABLE;
        }
        return flags;
    }

    private void startApp(Context context, int taskId) {
        try {
            context.startActivity(buildLaunchIntent(context, taskId));
        } catch (Exception e) {
            Log.e(TAG, "Failed to start activity from alarm", e);
        }
    }
}
