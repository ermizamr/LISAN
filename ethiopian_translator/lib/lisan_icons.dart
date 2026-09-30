import 'dart:math' as math;
import 'package:flutter/material.dart';

enum LisanIconType {
  spark,
  mic,
  volume,
  close,
  check,
  arrow,
  shield,
  brain,
}

class LisanIcon extends StatelessWidget {
  const LisanIcon(
    this.type, {
    super.key,
    this.size = 20,
    this.color,
    this.strokeWidth = 1.8,
  });

  final LisanIconType type;
  final double size;
  final Color? color;
  final double strokeWidth;

  @override
  Widget build(BuildContext context) {
    final effectiveColor = color ?? IconTheme.of(context).color ?? Colors.white;
    return CustomPaint(
      size: Size(size, size),
      painter: _LisanIconPainter(
        type: type,
        color: effectiveColor,
        strokeWidth: strokeWidth,
      ),
    );
  }
}

class _LisanIconPainter extends CustomPainter {
  const _LisanIconPainter({
    required this.type,
    required this.color,
    required this.strokeWidth,
  });

  final LisanIconType type;
  final Color color;
  final double strokeWidth;

  @override
  void paint(Canvas canvas, Size size) {
    final scale = size.width / 24.0;
    canvas.save();
    canvas.scale(scale, scale);

    final strokePaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;

    switch (type) {
      case LisanIconType.spark:
        final path = Path()
          ..moveTo(12, 2)
          ..lineTo(13.5, 7.1)
          ..lineTo(18, 9.7)
          ..lineTo(13.5, 12.3)
          ..lineTo(12, 18)
          ..lineTo(10.5, 12.3)
          ..lineTo(6, 9.7)
          ..lineTo(10.5, 7.1)
          ..close();
        final path2 = Path()
          ..moveTo(18.5, 15)
          ..lineTo(19.2, 17.3)
          ..lineTo(21, 18.3)
          ..lineTo(19.2, 19.4)
          ..lineTo(18.5, 21.7)
          ..lineTo(17.8, 19.4)
          ..lineTo(16, 18.3)
          ..lineTo(17.8, 17.3)
          ..close();
        canvas.drawPath(path, strokePaint);
        canvas.drawPath(path2, strokePaint);
        break;

      case LisanIconType.mic:
        final rect = RRect.fromRectAndRadius(
          const Rect.fromLTWH(9, 3, 6, 11),
          const Radius.circular(3),
        );
        canvas.drawRRect(rect, strokePaint);
        final arcPath = Path()
          ..arcTo(
            const Rect.fromLTWH(5.5, 4, 13, 13),
            0,
            math.pi,
            false,
          );
        canvas.drawPath(arcPath, strokePaint);
        canvas.drawLine(const Offset(12, 17), const Offset(12, 21), strokePaint);
        canvas.drawLine(const Offset(8.5, 21), const Offset(15.5, 21), strokePaint);
        break;

      case LisanIconType.volume:
        final horn = Path()
          ..moveTo(5, 10)
          ..lineTo(8, 10)
          ..lineTo(12, 7)
          ..lineTo(12, 17)
          ..lineTo(8, 14)
          ..lineTo(5, 14)
          ..close();
        canvas.drawPath(horn, strokePaint);
        final wave1 = Path()
          ..arcTo(
            const Rect.fromLTWH(11, 9, 8, 6),
            -math.pi / 2,
            math.pi,
            false,
          );
        canvas.drawPath(wave1, strokePaint);
        final wave2 = Path()
          ..arcTo(
            const Rect.fromLTWH(10, 6.5, 15, 11),
            -math.pi / 2,
            math.pi,
            false,
          );
        canvas.drawPath(wave2, strokePaint);
        break;

      case LisanIconType.close:
        canvas.drawLine(const Offset(6, 6), const Offset(18, 18), strokePaint);
        canvas.drawLine(const Offset(18, 6), const Offset(6, 18), strokePaint);
        break;

      case LisanIconType.check:
        final path = Path()
          ..moveTo(5, 12)
          ..lineTo(9.2, 16.2)
          ..lineTo(19, 6.5);
        canvas.drawPath(path, strokePaint);
        break;

      case LisanIconType.arrow:
        final path = Path()
          ..moveTo(9, 18)
          ..lineTo(15, 12)
          ..lineTo(9, 6);
        canvas.drawPath(path, strokePaint);
        break;

      case LisanIconType.shield:
        final path = Path()
          ..moveTo(12, 3)
          ..lineTo(5.5, 5.6)
          ..lineTo(5.5, 11.3)
          ..cubicTo(5.5, 15.6, 8.2, 19.1, 12, 21)
          ..cubicTo(15.8, 19.1, 18.5, 15.6, 18.5, 11.3)
          ..lineTo(18.5, 5.6)
          ..close();
        canvas.drawPath(path, strokePaint);
        final check = Path()
          ..moveTo(9.3, 12)
          ..lineTo(11.1, 13.8)
          ..lineTo(15, 9.8);
        canvas.drawPath(check, strokePaint);
        break;

      case LisanIconType.brain:
        final leftLobe = Path()
          ..moveTo(9.5, 5.5)
          ..cubicTo(7, 5.5, 4.7, 6.5, 4.7, 8)
          ..cubicTo(4.7, 10.5, 4.9, 13.8, 4.9, 13.8)
          ..cubicTo(6, 17, 10, 17, 10, 17)
          ..lineTo(10, 5.5);
        final rightLobe = Path()
          ..moveTo(14.5, 5.5)
          ..cubicTo(17, 5.5, 19.3, 6.5, 19.3, 8)
          ..cubicTo(19.3, 10.5, 19.1, 13.8, 19.1, 13.8)
          ..cubicTo(18, 17, 14, 17, 14, 17)
          ..lineTo(14, 5.5);
        canvas.drawPath(leftLobe, strokePaint);
        canvas.drawPath(rightLobe, strokePaint);
        canvas.drawLine(const Offset(8, 10), const Offset(10, 10), strokePaint);
        canvas.drawLine(const Offset(14, 13), const Offset(16, 13), strokePaint);
        canvas.drawLine(const Offset(8, 17), const Offset(8, 19), strokePaint);
        canvas.drawLine(const Offset(16, 17), const Offset(16, 19), strokePaint);
        break;
    }

    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant _LisanIconPainter oldDelegate) {
    return oldDelegate.type != type ||
        oldDelegate.color != color ||
        oldDelegate.strokeWidth != strokeWidth;
  }
}

enum LanguageSymbolType {
  glyph,
  tree,
  sun,
  star,
  globe,
}

class LanguageSymbolWidget extends StatelessWidget {
  const LanguageSymbolWidget({
    super.key,
    required this.symbol,
    this.size = 24,
    this.color = Colors.white,
  });

  final LanguageSymbolType symbol;
  final double size;
  final Color color;

  @override
  Widget build(BuildContext context) {
    if (symbol == LanguageSymbolType.glyph) {
      return Text(
        'ሀ',
        style: TextStyle(
          color: color,
          fontSize: size * 0.88,
          fontWeight: FontWeight.w700,
          fontFamily: 'sans',
          height: 1.0,
        ),
      );
    }

    return CustomPaint(
      size: Size(size, size),
      painter: _LanguageSymbolPainter(symbol: symbol, color: color),
    );
  }
}

class _LanguageSymbolPainter extends CustomPainter {
  const _LanguageSymbolPainter({required this.symbol, required this.color});

  final LanguageSymbolType symbol;
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final scale = size.width / 24.0;
    canvas.save();
    canvas.scale(scale, scale);

    final strokePaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.7
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;

    switch (symbol) {
      case LanguageSymbolType.glyph:
        break;

      case LanguageSymbolType.tree:
        canvas.drawLine(const Offset(12, 4), const Offset(12, 20), strokePaint);
        canvas.drawLine(const Offset(7, 18), const Offset(17, 18), strokePaint);
        final tier1 = Path()
          ..moveTo(12, 6)
          ..lineTo(7, 11)
          ..lineTo(17, 11)
          ..close();
        canvas.drawPath(tier1, strokePaint);
        final tier2 = Path()
          ..moveTo(12, 10)
          ..lineTo(5, 16)
          ..lineTo(19, 16)
          ..close();
        canvas.drawPath(tier2, strokePaint);
        break;

      case LanguageSymbolType.sun:
        canvas.drawCircle(const Offset(12, 12), 4, strokePaint);
        canvas.drawLine(const Offset(12, 3), const Offset(12, 6), strokePaint);
        canvas.drawLine(const Offset(12, 18), const Offset(12, 21), strokePaint);
        canvas.drawLine(const Offset(3, 12), const Offset(6, 12), strokePaint);
        canvas.drawLine(const Offset(18, 12), const Offset(21, 12), strokePaint);
        canvas.drawLine(const Offset(5.6, 5.6), const Offset(7.7, 7.7), strokePaint);
        canvas.drawLine(const Offset(16.3, 16.3), const Offset(18.4, 18.4), strokePaint);
        canvas.drawLine(const Offset(18.4, 5.6), const Offset(16.3, 7.7), strokePaint);
        canvas.drawLine(const Offset(7.7, 16.3), const Offset(5.6, 18.4), strokePaint);
        break;

      case LanguageSymbolType.star:
        final star = Path()
          ..moveTo(12, 3)
          ..lineTo(14.1, 9.5)
          ..lineTo(21, 9.5)
          ..lineTo(15.5, 13.5)
          ..lineTo(17.6, 20)
          ..lineTo(12, 16)
          ..lineTo(6.4, 20)
          ..lineTo(8.5, 13.5)
          ..lineTo(3, 9.5)
          ..lineTo(9.9, 9.5)
          ..close();
        canvas.drawPath(star, strokePaint);
        break;

      case LanguageSymbolType.globe:
        canvas.drawCircle(const Offset(12, 12), 9, strokePaint);
        canvas.drawLine(const Offset(3, 12), const Offset(21, 12), strokePaint);
        final oval = Rect.fromCenter(center: const Offset(12, 12), width: 9, height: 18);
        canvas.drawOval(oval, strokePaint);
        break;
    }

    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant _LanguageSymbolPainter oldDelegate) {
    return oldDelegate.symbol != symbol || oldDelegate.color != color;
  }
}
