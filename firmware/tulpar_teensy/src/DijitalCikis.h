#pragma once

namespace tulpar {

// Basit bir dijital cikis pinini soyutlar (role, LED vb.) - boylece
// LazerKatmani gercek donanim olmadan PC'de (mock ile) test edilebilir.
class DijitalCikis {
 public:
  virtual ~DijitalCikis() = default;
  virtual void yaz(bool yuksek) = 0;
};

}  // namespace tulpar
