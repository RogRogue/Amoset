# Amöset Discord Bot

Discord sunucunuz için Valorant maç geçmişi görüntüleme botu.

## Özellikler
- Oyuncuların son 5 maçını görüntüleme
- Rekabetçi, Derecesiz ve Tam Gaz modları için maç geçmişi
- K/D/A, harita ve skor bilgileri
- Ajan bilgisi ve maç sonucu

## Kurulum
1. Repository'yi klonlayın
2. `.env` dosyası oluşturun ve şu değişkenleri ekleyin:
   ```
   DISCORD_TOKEN=your_discord_token
   HENRIK_API_KEY=your_henrik_api_key
   ```
3. Gerekli paketleri yükleyin:
   ```
   pip install -r requirements.txt
   ```
4. Botu çalıştırın:
   ```
   python bot.py
   ```

## Komutlar
- `/valorant <oyuncu#tag>` - Belirtilen oyuncunun maç geçmişini gösterir
- `/help` - Komut listesini gösterir 