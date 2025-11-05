use i18n_macros::i18n_command;
use serenity::all::{Channel, Mentionable};

use crate::bot_data::{Context, Error};

/// Returns true if joined, false if already connected
async fn _join(ctx: &Context<'_>, channel_id: Option<Channel>) -> Result<bool, Error> {
    use crate::i18n::t;
    let data = ctx.data();
    let lava_client = data.lavalink.clone();
    let manager = data.manager.clone();

    let guild_id = ctx.guild_id().unwrap();

    if lava_client.get_player_context(guild_id.get()).is_none() {
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
                        return Ok(false);
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

                lava_client
                    // The turbofish here is Optional, but it helps to figure out what type to
                    // provide in `PlayerContext::data()`
                    //
                    // While a tuple is used here as an example, you are free to use a custom
                    // public structure with whatever data you wish.
                    // This custom data is also present in the Client if you wish to have the
                    // shared data be more global, rather than centralized to each player.
                    // .create_player_context_with_data::<(ChannelId, std::sync::Arc<serenity::all::Http>)>(
                    .create_player_context(
                        guild_id.get(),
                        connection_info,
                        // std::sync::Arc::new((connect_to, ctx.serenity_context().http.clone())),
                    )
                    .await?;

                ctx.say(t!(
                    ctx,
                    commands::music::join::Joined,
                    channel = &connect_to.mention().to_string()
                ))
                .await?;

                return Ok(true);
            }
            Err(why) => {
                ctx.say(t!(
                    ctx,
                    commands::music::join::ErrorJoining,
                    error = &why.to_string()
                ))
                .await?;
                return Err(why.into());
            }
        }
    }

    ctx.say(t!(ctx, commands::music::join::AlreadyInChannel))
        .await?;
    Ok(false)
}

#[i18n_command(
    prefix_command,
    slash_command,
    guild_only,
    aliases("p", "toca")
    category = "Music",
)]
pub async fn play(ctx: Context<'_>, #[rest] query: String) -> Result<(), Error> {
    ctx.reply("play").await?;
    Ok(())
}

// impl poise::PopArgument for ChannelId {

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
    _join(&ctx, channel.clone()).await?;

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
