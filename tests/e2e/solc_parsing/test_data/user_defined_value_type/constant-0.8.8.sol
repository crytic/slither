type T is int224;

contract C {
  T constant public s = T.wrap(int224(165521356710917456517261742455526507355687727119203895813322792776));
  T constant public t = s;
  int224 constant public u = T.unwrap(t);
}
