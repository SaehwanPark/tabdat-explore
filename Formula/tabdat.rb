class Tabdat < Formula
  include Language::Python::Virtualenv

  desc "Terminal-native exploratory data analysis tool for modern tabular data"
  homepage "https://github.com/SaehwanPark/tabdat-explore"
  url "https://github.com/SaehwanPark/tabdat-explore/archive/refs/tags/v0.23.0.tar.gz"
  license "AGPL-3.0-or-later"
  head "https://github.com/SaehwanPark/tabdat-explore.git", branch: "main"

  depends_on "python@3.13"

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "TabDat Environment & Capability Health", shell_output("#{bin}/tabdat doctor")
  end
end
