import xbmc
import xbmcgui

def run():
    # Metadaten aus aktuellem Kontext abrufen
    title = xbmc.getInfoLabel("ListItem.Title")
    file_path = xbmc.getInfoLabel("ListItem.FileNameAndPath")
    if not file_path:
        xbmcgui.Dialog().notification("Watchlist", "Kein gültiger Eintrag.", xbmcgui.NOTIFICATION_WARNING, 2000)
        return

    # Watchlist-Addon ausführen
    xbmc.executebuiltin(f'RunPlugin(plugin://plugin.video.wl/?action=add)')
    xbmcgui.Dialog().notification("Watchlist", f"'{title}' hinzugefügt", xbmcgui.NOTIFICATION_INFO, 2000)

if __name__ == '__main__':
    #run()
    xbmc.executebuiltin(f'RunPlugin(plugin://plugin.video.wl/?action=add)')
    
