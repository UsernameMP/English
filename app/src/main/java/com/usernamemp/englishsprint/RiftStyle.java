package com.usernamemp.englishsprint;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.ColorFilter;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.Shader;
import android.graphics.Typeface;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.view.MotionEvent;
import android.view.View;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.function.Consumer;

/**
 * Rift visual language. Systematic shapes, color, typography and playful
 * native-canvas artwork keep screens lightweight, offline and responsive.
 * No changes to learning, activity history or daily activity storage.
 */
public final class RiftStyle {
    private RiftStyle() {}

    public static final int BACKGROUND = Color.rgb(246, 248, 253);
    public static final int INK = Color.rgb(20, 26, 50);
    public static final int MUTED = Color.rgb(104, 115, 143);
    public static final int BLUE = Color.rgb(79, 76, 239);
    public static final int VIOLET = Color.rgb(132, 91, 247);
    public static final int CYAN = Color.rgb(54, 215, 245);
    public static final int NAVY = Color.rgb(11, 15, 45);
    public static final int STROKE = Color.rgb(231, 235, 247);
    public static final int GOOD = Color.rgb(26, 167, 124);
    public static final int SURFACE = Color.WHITE;

    public static int dp(Context c, float value) {
        return Math.round(value * c.getResources().getDisplayMetrics().density);
    }

    public static GradientDrawable shape(Context c, int color, int radius, int border, int borderColor) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(color);
        drawable.setCornerRadius(dp(c, radius));
        if (border > 0) drawable.setStroke(dp(c, border), borderColor);
        return drawable;
    }

    public static GradientDrawable gradient(Context c, int radius, int... colors) {
        GradientDrawable drawable = new GradientDrawable(
                GradientDrawable.Orientation.TL_BR, colors);
        drawable.setCornerRadius(dp(c, radius));
        return drawable;
    }

    public static void raise(View view, float dp) {
        view.setElevation(dp(view.getContext(), dp));
    }

    public static TextView text(Context c, String value, int size, int color, boolean bold) {
        TextView text = new TextView(c);
        text.setText(value);
        text.setTextSize(size);
        text.setTextColor(color);
        text.setFontFeatureSettings("kern");
        text.setTypeface(Typeface.create(bold ? "sans-serif-medium" : "sans-serif",
                bold ? Typeface.BOLD : Typeface.NORMAL));
        text.setIncludeFontPadding(false);
        return text;
    }

    public static TextView pill(Context c, String label, int foreground, int background) {
        TextView view = text(c, label, 12, foreground, true);
        view.setPadding(dp(c, 12), dp(c, 8), dp(c, 12), dp(c, 8));
        view.setBackground(shape(c, background, 20, 0, Color.TRANSPARENT));
        return view;
    }

    public static Drawable cosmic(Context context, int radius) {
        return new CosmicDrawable(context, radius);
    }

    private static final class CosmicDrawable extends Drawable {
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final float corner;
        private int alpha = 255;
        CosmicDrawable(Context c, int radius) { corner = dp(c, radius); }

        @Override public void draw(Canvas canvas) {
            Rect rect = getBounds();
            if (rect.isEmpty()) return;
            float w = rect.width(), h = rect.height();
            int saved = canvas.save();
            Path clip = new Path();
            clip.addRoundRect(new RectF(rect), corner, corner, Path.Direction.CW);
            canvas.clipPath(clip);
            paint.setShader(new LinearGradient(0, 0, w, h,
                    new int[]{Color.rgb(13, 21, 66), Color.rgb(61, 45, 149),
                            Color.rgb(18, 26, 76)}, null, Shader.TileMode.CLAMP));
            paint.setAlpha(alpha);
            canvas.drawRect(rect, paint);
            paint.setShader(null);
            paint.setStyle(Paint.Style.FILL);
            // Off-centre portal rings make the header recognisably Rift.
            float cx = w * .94f, cy = h * .36f;
            for (int i = 5; i >= 0; i--) {
                paint.setColor(Color.argb(24 + i * 4, 64 + 8 * i, 177, 245));
                paint.setStyle(Paint.Style.STROKE);
                paint.setStrokeWidth(2.2f + (5-i) * 1.3f);
                canvas.drawCircle(cx, cy, w * (.21f + i * .055f), paint);
            }
            paint.setStyle(Paint.Style.FILL);
            for (int i = 0; i < 36; i++) {
                float x = w * ((i * 67 % 97) / 97f);
                float y = h * ((i * 43 % 89) / 89f);
                paint.setColor(Color.argb(i % 5 == 0 ? 155 : 75, 178, 219, 255));
                canvas.drawCircle(x, y, i % 6 == 0 ? 2.2f : 1f, paint);
            }
            canvas.restoreToCount(saved);
        }
        @Override public void setAlpha(int a) { alpha = a; invalidateSelf(); }
        @Override public void setColorFilter(ColorFilter f) { paint.setColorFilter(f); invalidateSelf(); }
        @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
    }

    /** A radial progress emblem for completion, with a distinctive Rift portal. */
    public static final class ScoreRing extends View {
        private final Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final int percent;
        public ScoreRing(Context context, int percent) {
            super(context);
            this.percent = Math.max(0, Math.min(100, percent));
            setContentDescription(percent + "%");
        }
        @Override protected void onMeasure(int w, int h) {
            int s = dp(getContext(), 166);
            setMeasuredDimension(resolveSize(s, w), resolveSize(s, h));
        }
        @Override protected void onDraw(Canvas c) {
            float cx=getWidth()/2f, cy=getHeight()/2f;
            float r=Math.min(getWidth(),getHeight())*.39f;
            p.setStyle(Paint.Style.STROKE); p.setStrokeCap(Paint.Cap.ROUND); p.setStrokeWidth(dp(getContext(),12));
            p.setColor(STROKE); c.drawCircle(cx,cy,r,p);
            p.setColor(percent>=75?GOOD:BLUE);
            c.drawArc(cx-r,cy-r,cx+r,cy+r,-90,percent*3.6f,false,p);
            p.setStyle(Paint.Style.FILL);
            p.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));
            p.setTextAlign(Paint.Align.CENTER);
            p.setColor(INK); p.setTextSize(dp(getContext(),35));
            c.drawText(percent+"%",cx,cy+dp(getContext(),10),p);
        }
    }

    /** Touch-accessible prerequisite map: actual Atlas edges and mastery data. */
    public static final class KnowledgeMap extends View {
        private final List<String> ids;
        private final List<String> labels;
        private final List<Integer> states;
        private final List<KnowledgeRelation> relations;
        private final Consumer<String> onSelect;
        private final Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final List<RectF> hitBoxes = new ArrayList<>();
        private int rowHeight;

        public KnowledgeMap(Context c, List<String> ids, List<String> labels, List<Integer> states,
                            List<KnowledgeRelation> relations, Consumer<String> onSelect) {
            super(c);
            this.ids=ids; this.labels=labels; this.states=states;
            this.relations=relations; this.onSelect=onSelect;
            rowHeight=dp(c,104);
            setClickable(true);
            setContentDescription("Knowledge atlas. Touch a node to view its topic.");
        }
        @Override protected void onMeasure(int w, int h) {
            int width=MeasureSpec.getSize(w);
            int rows=(ids.size()+1)/2;
            setMeasuredDimension(width, Math.max(dp(getContext(),60), rows*rowHeight+dp(getContext(),34)));
        }
        private float x(int i) {
            float w=getWidth();
            return (i%2==0 ? .285f : .715f)*w;
        }
        private float y(int i) { return dp(getContext(),24)+(i/2)*rowHeight + rowHeight*.44f; }

        @Override protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            hitBoxes.clear();
            float w=getWidth(), radius=dp(getContext(),17);
            p.setStyle(Paint.Style.STROKE); p.setStrokeWidth(dp(getContext(),2));
            for(int i=0;i<ids.size();i++) {
                for(KnowledgeRelation edge:relations) {
                    if(!edge.to.equals(ids.get(i)) || !"requires".equals(edge.type)) continue;
                    int from=ids.indexOf(edge.from);
                    if(from<0)continue;
                    p.setColor(Color.rgb(196,205,238));
                    canvas.drawLine(x(from),y(from),x(i),y(i),p);
                }
                if(i>0) {
                    p.setColor(Color.rgb(224,229,245));
                    canvas.drawLine(x(i-1),y(i-1),x(i),y(i),p);
                }
            }
            p.setStyle(Paint.Style.FILL);
            float hw=Math.min(w*.205f,dp(getContext(),95));
            float hh=dp(getContext(),38);
            for(int i=0;i<ids.size();i++){
                float cx=x(i),cy=y(i);
                RectF outer=new RectF(cx-hw,cy-hh,cx+hw,cy+hh);
                hitBoxes.add(outer);
                p.setColor(STROKE);
                canvas.drawRoundRect(new RectF(outer.left,outer.top+dp(getContext(),4),
                        outer.right,outer.bottom+dp(getContext(),4)),radius,radius,p);
                boolean strong=states.get(i)>=2;
                p.setColor(strong?Color.rgb(232,246,252):SURFACE);
                canvas.drawRoundRect(outer,radius,radius,p);
                p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(dp(getContext(),1));
                p.setColor(strong?CYAN:STROKE);
                canvas.drawRoundRect(outer,radius,radius,p);
                p.setStyle(Paint.Style.FILL);
                p.setColor(states.get(i)>=3?GOOD:states.get(i)==2?BLUE:
                        states.get(i)==1?VIOLET:MUTED);
                canvas.drawCircle(cx,cy-hh+dp(getContext(),8),dp(getContext(),4),p);
                p.setColor(INK);
                p.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
                p.setTextSize(dp(getContext(),12));
                p.setTextAlign(Paint.Align.CENTER);
                String label=labels.get(i);
                float max=hw*1.85f;
                while(label.length()>1 && p.measureText(label)>max) label=label.substring(0,label.length()-2)+"…";
                canvas.drawText(label,cx,cy+dp(getContext(),9),p);
            }
        }
        @Override public boolean onTouchEvent(MotionEvent event) {
            if(event.getAction()==MotionEvent.ACTION_DOWN) return true;
            if(event.getAction()==MotionEvent.ACTION_UP) {
                for(int i=0;i<hitBoxes.size();i++) {
                    if(hitBoxes.get(i).contains(event.getX(),event.getY())) {
                        performClick(); onSelect.accept(ids.get(i)); return true;
                    }
                }
                performClick(); return true;
            }
            return super.onTouchEvent(event);
        }
        @Override public boolean performClick() { super.performClick(); return true; }
    }
}
