import 'package:flutter_test/flutter_test.dart';

import 'package:novi_flutter_app/main.dart';

void main() {
  testWidgets('app shows sorter dashboard', (WidgetTester tester) async {
    await tester.pumpWidget(const NoviSorterApp());

    expect(find.text('Novi Sorter Monitor'), findsOneWidget);
    expect(find.text('System Status'), findsOneWidget);
    expect(find.text('Ready'), findsOneWidget);
  });
}
