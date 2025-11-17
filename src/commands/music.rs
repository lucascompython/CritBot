use i18n_macros::i18n_command;
use lavalink_rs::prelude::{PlayerContext, SearchEngines, TrackInQueue, TrackLoadData};
use serenity::all::{Channel, Mentionable};

use crate::{
    bot_data::{Context, Error, LavalinkData},
    i18n::get_locale,
};
// TODO: search command, set the channel activity to the current track

/// Returns true if joined, false if already connected
/// If from_play is true, then won't send the "already connected" message
async fn _join(
    ctx: &Context<'_>,
    channel_id: Option<Channel>,
    from_play: bool,
) -> Result<Option<PlayerContext>, Error> {
    use crate::i18n::t;
    let data = ctx.data();
    let lava_client = data.lavalink.clone();
    let manager = data.manager.clone();

    let guild_id = ctx.guild_id().unwrap();

    match lava_client.get_player_context(guild_id.get()) {
        Some(player) => {
            if !from_play {
                ctx.say(t!(ctx, commands::music::join::AlreadyInChannel))
                    .await?;
            }
            Ok(Some(player))
        }
        None => {
            let connect_to = match channel_id {
                Some(x) => x.id().expect_channel(),
                None => {
                    let guild = ctx.guild().unwrap().clone();
                    let user_channel_id = guild
                        .voice_states
                        .get(&ctx.author().id)
                        .and_then(|voice_state| voice_state.channel_id);

                    match user_channel_id {
                        Some(channel) => channel,
                        None => {
                            ctx.say(t!(ctx, commands::music::join::YouNotInChannel))
                                .await?;
                            return Ok(None);
                        }
                    }
                }
            };

            let handler = manager.join_gateway(guild_id, connect_to).await;

            match handler {
                Ok((connection_info, _)) => {
                    // having to do this is weird
                    let connection_info = lavalink_rs::model::player::ConnectionInfo {
                        endpoint: connection_info.endpoint,
                        token: connection_info.token,
                        session_id: connection_info.session_id,
                    };

                    let locale = get_locale(ctx);

                    let player = lava_client
                        // The turbofish here is Optional, but it helps to figure out what type to
                        // provide in `PlayerContext::data()`
                        //
                        // While a tuple is used here as an example, you are free to use a custom
                        // public structure with whatever data you wish.
                        // This custom data is also present in the Client if you wish to have the
                        // shared data be more global, rather than centralized to each player.
                        .create_player_context_with_data::<LavalinkData>(
                            // .create_player_context(
                            // TODO: also check this
                            guild_id.get(),
                            connection_info,
                            std::sync::Arc::new(LavalinkData {
                                channel_id: ctx.channel_id(),
                                http: ctx.serenity_context().http.clone(),
                                locale,
                            }),
                        )
                        .await?;

                    ctx.say(t!(
                        ctx,
                        commands::music::join::Joined,
                        channel = &connect_to.mention().to_string()
                    ))
                    .await?;

                    Ok(Some(player))
                }
                Err(why) => {
                    ctx.say(t!(
                        ctx,
                        commands::music::join::ErrorJoining,
                        error = &why.to_string()
                    ))
                    .await?;
                    Err(why.into())
                }
            }
        }
    }
}

#[i18n_command(
    prefix_command,
    slash_command,
    guild_only,
    aliases("p", "toca")
    category = "Music",
)]
pub async fn play(ctx: Context<'_>, #[rest] query: String) -> Result<(), Error> {
    let player = _join(&ctx, None, true).await?;

    let player = match player {
        Some(x) => x,
        None => {
            return Ok(());
        }
    };

    let lava_client = &ctx.data().lavalink;

    let original_query = query.clone();

    let query = if query.starts_with("http") {
        query
    } else {
        SearchEngines::YouTube.to_query(&query)?
    };

    let guild_id = ctx.guild_id().unwrap().get();

    let loaded_tracks = lava_client.load_tracks(guild_id, &query).await?;

    let mut playlist_info = None;

    let mut tracks: Vec<TrackInQueue> = match loaded_tracks.data {
        Some(TrackLoadData::Track(x)) => vec![x.into()],
        Some(TrackLoadData::Search(x)) => vec![x[0].clone().into()], // TODO: check this
        Some(TrackLoadData::Playlist(x)) => {
            playlist_info = Some(x.info);
            x.tracks.iter().map(|x| x.clone().into()).collect()
        }

        _ => {
            ctx.say(t!(NotFound, query = &original_query)).await?;
            return Ok(());
        }
    };

    if let Some(info) = playlist_info {
        ctx.say(t!(AddedPlaylist, name = &info.name)).await?;
    } else {
        let track = &tracks[0].track;

        if let Ok(player_data) = player.get_player().await
            && player_data.track.is_some()
            && let Some(uri) = &track.info.uri
        {
            ctx.say(t!(
                AddedTrack,
                author = &track.info.author,
                title = &track.info.title,
                uri = uri
            ))
            .await?;
        } else if track.info.uri.is_none() {
            // TODO: this if is most likely useless
            ctx.say("`track.info.uri` = None (play command)").await?;
        }
    }

    for i in &mut tracks {
        i.track.user_data = Some(serde_json::json!({"requester_id": ctx.author().id.get()}));
    }

    let queue = player.get_queue();
    queue.append(tracks.into())?;

    if let Ok(player_data) = player.get_player().await
        && player_data.track.is_none()
        && queue.get_track(0).await.is_ok_and(|x| x.is_some())
    {
        player.skip()?;
    }

    Ok(())
}

#[i18n_command(
    slash_command,
    prefix_command,
    guild_only,
    aliases("entra"),
    category = "Music"
)]
pub async fn join(
    ctx: Context<'_>,
    #[channel_types("Voice")] channel: Option<serenity::model::channel::Channel>,
) -> Result<(), Error> {
    _join(&ctx, channel.clone(), false).await?;

    Ok(())
}
#[i18n_command(
    slash_command,
    prefix_command,
    guild_only,
    aliases("sai"),
    category = "Music"
)]
pub async fn leave(ctx: Context<'_>) -> Result<(), Error> {
    let guild_id = ctx.guild_id().unwrap();

    let data = ctx.data();
    let manager = data.manager.clone();

    let lava_client = data.lavalink.clone();
    lava_client.delete_player(guild_id.get()).await?;

    if manager.get(guild_id).is_some() {
        manager.remove(guild_id).await?;
        ctx.say(t!(Left)).await?; // TODO: react to the message
        return Ok(());
    }

    ctx.say(t!(NotInChannel)).await?;

    Ok(())
}
