import discord.ext.commands as discord_cmds
import myanimebot.globals as globals


@discord_cmds.command(name="top")
async def top_cmd(ctx, *, keyword):
    ''' Processes the command "top" and returns statistics on registered feeds '''

    # TODO Redo this function

    if keyword is None:
        try:
            cursor = globals.conn.cursor(buffered=True)
            cursor.execute("SELECT * FROM v_Top")
            data = cursor.fetchone()
            
            if data is None: await ctx.send("It seems that there is no statistics... (what happened?!)")
            else:
                topText = "**__Here is the global statistics of this bot:__**\n\n"
                
                while data is not None:
                    topText += " - " + str(data[0]) + ": " + str(data[1]) + "\n"
                        
                    data = cursor.fetchone()
                    
                cursor = globals.conn.cursor(buffered=True)
                cursor.execute("SELECT * FROM v_TotalFeeds")
                data = cursor.fetchone()
                
                topText += "\n***Total user entry***: " + str(data[0])
                
                cursor = globals.conn.cursor(buffered=True)
                cursor.execute("SELECT * FROM v_TotalAnimes")
                data = cursor.fetchone()
                
                topText += "\n***Total unique manga/anime***: " + str(data[0])
                
                await ctx.send(topText)
            
            cursor.close()
        except Exception as e:
            globals.logger.warning("An error occured while displaying the global top: " + str(e))
            await ctx.send("Unable to reply to your request at the moment...")
    else:
        globals.logger.info("Displaying the global top for the keyword: " + keyword)
        
        try:
            cursor = globals.conn.cursor(buffered=True)
            cursor.callproc('sp_UsersPerKeyword', [str(keyword), '20'])
            for result in cursor.stored_results():
                data = result.fetchone()
                
                if data is None: await ctx.send("It seems that there is no statistics for the keyword **" + keyword + "**.")
                else:
                    topKeyText = "**__Here is the statistics for the keyword " + keyword + ":__**\n\n"
                    
                    while data is not None:
                        topKeyText += " - " + str(data[0]) + ": " + str(data[1]) + "\n"
                            
                        data = result.fetchone()
                        
                    await ctx.send(topKeyText)
                
            cursor.close()
        except Exception as e:
            globals.logger.warning("An error occured while displaying the global top for keyword '" + keyword + "': " + str(e))
            await ctx.send("Unable to reply to your request at the moment...")
