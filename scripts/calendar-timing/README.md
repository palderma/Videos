# التوقيت قبل المناسبة (موشن تقويم 3D)

- `cal3d.py`: تقويم ثلاثي الأبعاد (كاميرا منظور، حلقات wire-o، تقليب صفحات منحنية بإضاءة وظلال، Motion Blur) -> PNG بشفافية.
- `comp.py`: التركيب (خلفية، نصوص، كبسولات، شعار، إطار) عبر kf -> MP4 + سكربت After Effects.
- `audio_cal.py`: موسيقى + تقليب ورق + تكتكة ساعة.
- `tl.py`: التوقيتات. `textures.py`: تصميم الصفحات.

التشغيل: `python3 comp.py assets`، ثم `python3 cal3d.py calseq 0 450`، ثم `python3 comp.py render 0 450 out.mp4`، و`python3 audio_cal.py`.
