use lavalink_rs::{hook, model::events, prelude::*};
use tracing::{debug, info};

use crate::bot_data::LavalinkData;

// The #[hook] macro transforms:
// ```rs
// #[hook]
// async fn foo(a: A) -> T {
//     ...
// }
// ```
// into
// ```rs
// fn foo<'a>(a: A) -> Pin<Box<dyn Future<Output = T> + Send + 'a>> {
//     Box::pin(async move {
//         ...
//     })
// }
// ```
//
// This allows the asynchronous function to be stored in a structure.

#[hook]
pub async fn raw_event(_: LavalinkClient, session_id: String, event: &serde_json::Value) {
    if (event["op"].as_str() == Some("event") || event["op"].as_str() == Some("playerUpdate"))
        && event["state"].as_object().is_none()
    {
        info!("{:?} -> {:?}", session_id, event);
    }
}

#[hook]
pub async fn ready_event(client: LavalinkClient, session_id: String, event: &events::Ready) {
    client.delete_all_player_contexts().await.unwrap();
    info!("{:?} -> {:?}", session_id, event);
}

#[hook]
pub async fn track_start(client: LavalinkClient, _session_id: String, event: &events::TrackStart) {
    let player_context = client.get_player_context(event.guild_id).unwrap();
    let data = player_context.data::<LavalinkData>().unwrap();
    let (channel_id, http) = (&data.channel_id, &data.http);

    let msg = {
        let track = &event.track;
        let requester_id = &track.user_data.as_ref().unwrap()["requester_id"];

        if let Some(uri) = &track.info.uri {
            // TODO: probably create a macro rule for this use case
            let now_playing_template =
                crate::i18n::translations::commands::music::play::Trans::NowPlaying;
            now_playing_template.translate(
                data.locale,
                &[
                    ("author", &track.info.author),
                    ("title", &track.info.title),
                    ("uri", uri),
                    ("requester_id", &requester_id.as_u64().unwrap().to_string()),
                ],
            )
        } else {
            "track.info.uri = None (track_start event)".to_string()
        }
    };

    channel_id.say(http, msg).await.unwrap();
}

#[hook]
pub async fn track_end(client: LavalinkClient, _session_id: String, event: &events::TrackEnd) {
    let player_context = client.get_player_context(event.guild_id).unwrap();
    debug!(
        "Songs left in queue: {:?}",
        player_context.get_queue().get_count().await
    );
}
