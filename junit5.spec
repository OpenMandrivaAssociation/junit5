Name:		junit5
Version:	5.14.4
Release:	1
%global platform_ver 1.14.4
Summary:	JUnit 5 platform, Jupiter, and vintage engines
Group:		Development/Java
License:	EPL-2.0
URL:		https://junit.org/junit5/
Source0:	https://github.com/junit-team/junit-framework/archive/refs/tags/r%{version}.tar.gz#/junit-framework-%{version}.tar.gz
BuildArch:	noarch
BuildRequires:	python
BuildRequires:	maven
BuildRequires:	maven-components >= 3.10.0
BuildRequires:	java-current-devel
BuildRequires:	mvn(org.apiguardian:apiguardian-api)
BuildRequires:	apiguardian >= 1.1.2
Requires:	apiguardian >= 1.1.2
BuildRequires:	mvn(org.opentest4j:opentest4j)
BuildRequires:	opentest4j >= 1.3.0
Requires:	opentest4j >= 1.3.0
BuildRequires:	mvn(junit:junit)
BuildRequires:	junit >= 1:4.13.2
Requires:	junit >= 1:4.13.2
BuildRequires:	mvn(org.hamcrest:hamcrest-core)
BuildRequires:	hamcrest >= 3.0
Requires:	hamcrest >= 3.0
BuildSystem:	maven

%description
JUnit 5.14.4 as separate jars: platform commons, engine, and launcher
1.14.4, Jupiter API and engine 5.14.4, and the vintage engine that runs
JUnit 4 tests on the platform. The upstream build is Gradle. This
package writes a parentless Maven reactor, generates JRE.java from the
upstream version list, and skips params, suite, and console. Tests need
the Jupiter test fixtures, so they are not run.

%prep
%autosetup -n junit-framework-r%{version}
rm -rf junit-jupiter-api/src/main/kotlin
python - <<'PY'
from pathlib import Path
def parse_jres(path):
    jres = []
    current = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("- version:"):
            if current:
                jres.append(current)
            current = {"version": int(line.split(":", 1)[1].strip()), "since": None}
        elif line.startswith("since:") and current:
            current["since"] = line.split(":", 1)[1].strip().strip("'\"")
    if current:
        jres.append(current)
    return jres


def render_jre(jres, header):
    see = "\n".join(" * @see #JAVA_{0}".format(item["version"]) for item in jres)
    constants = []
    for item in jres:
        version = item["version"]
        since = item["since"]
        if since:
            block = (
                "\t/**\n"
                "\t * Java {version}.\n"
                "\t *\n"
                "\t * @since {since}\n"
                "\t */\n"
                '\t@API(status = STABLE, since = "{since}")\n'
                "\tJAVA_{version}({version}),"
            ).format(version=version, since=since)
        else:
            block = (
                "\t/**\n"
                "\t * Java {version}.\n"
                "\t */\n"
                "\tJAVA_{version}({version}),"
            ).format(version=version)
        constants.append(block)
    parts = []
    for index, item in enumerate(jres):
        link = "{{@link #JAVA_{0}}}".format(item["version"])
        if index == len(jres) - 1:
            parts.append("or " + link + ".")
        else:
            piece = link + ","
            if index - (index // 3) * 3 == 1:
                piece += "\n\t * "
            else:
                piece += " "
            parts.append(piece)
    other = "".join(parts)
    cases = "\n".join(
        "\t\t\tcase {0}:\n\t\t\t\treturn JAVA_{0};".format(item["version"]) for item in jres
    )
    body = """{header}
package org.junit.jupiter.api.condition;

import static org.apiguardian.api.API.Status.DEPRECATED;
import static org.apiguardian.api.API.Status.MAINTAINED;
import static org.apiguardian.api.API.Status.STABLE;

import java.lang.reflect.Method;

import org.apiguardian.api.API;
import org.junit.platform.commons.logging.Logger;
import org.junit.platform.commons.logging.LoggerFactory;
import org.junit.platform.commons.support.ReflectionSupport;
import org.junit.platform.commons.util.StringUtils;

/**
 * Enumeration of Java Runtime Environment (JRE) versions.
 *
 * <p>If the current JRE version can be detected but is not one of the predefined
 * constants in this enum, {{@link #OTHER}} will be considered to be the
 * {{@linkplain #isCurrentVersion current JRE version}}. If the current JRE version
 * cannot be detected &mdash; for example, if the {{@code java.version}} JVM system
 * property is undefined &mdash; {{@link #UNDEFINED}} will be considered to be the
 * current JRE version.
 *
 * @since 5.1
{see}
 * @see #OTHER
 * @see EnabledOnJre
 * @see DisabledOnJre
 * @see EnabledForJreRange
 * @see DisabledForJreRange
 */
@API(status = STABLE, since = "5.1")
public enum JRE {{

	/**
	 * An undefined JRE version.
	 *
	 * <p>This constant is used by JUnit as a default configuration value but is
	 * not intended to be used by users.
	 *
	 * <p>This constant returns {{@code -1}} for its {{@linkplain #version() version}}.
	 *
	 * @since 5.12
	 */
	@API(status = MAINTAINED, since = "5.13.3")
	UNDEFINED(-1),

{constants}

	/**
	 * A JRE version other than {other}
	 *
	 * <p>This constant returns {{@link Integer#MAX_VALUE}} for its
	 * {{@linkplain #version() version}}. To retrieve the actual version number,
	 * use {{@link #currentVersionNumber()}}.
	 */
	OTHER(Integer.MAX_VALUE);

	static final int UNDEFINED_VERSION = -1;

	static final int MINIMUM_VERSION = 8;

	private static final Logger logger = LoggerFactory.getLogger(JRE.class);

	private static final int CURRENT_VERSION = determineCurrentVersion();

	private static final JRE CURRENT_JRE = determineCurrentJre(CURRENT_VERSION);

	private static int determineCurrentVersion() {{
		String javaVersion = System.getProperty("java.version");
		boolean javaVersionIsBlank = StringUtils.isBlank(javaVersion);

		if (javaVersionIsBlank) {{
			logger.debug(
				() -> "JVM system property 'java.version' is undefined. It is therefore not possible to detect Java 8.");
		}}

		if (!javaVersionIsBlank && javaVersion.startsWith("1.8")) {{
			return 8;
		}}

		try {{
			// java.lang.Runtime.version() is a static method available on Java 9+
			// that returns an instance of java.lang.Runtime.Version which has the
			// following method: public int major()
			Method versionMethod = Runtime.class.getMethod("version");
			Object version = ReflectionSupport.invokeMethod(versionMethod, null);
			Method majorMethod = version.getClass().getMethod("major");
			return (int) ReflectionSupport.invokeMethod(majorMethod, version);
		}}
		catch (Exception ex) {{
			logger.debug(ex, () -> "Failed to determine the current JRE version via java.lang.Runtime.Version.");
		}}

		return UNDEFINED_VERSION;
	}}

	private static JRE determineCurrentJre(int currentVersion) {{
		switch (currentVersion) {{
			case UNDEFINED_VERSION:
				return UNDEFINED;
{cases}
			default:
				return OTHER;
		}}
	}}

	private final int version;

	private JRE(int version) {{
		this.version = version;
	}}

	/**
	 * Get the version of <em>this</em> {{@code JRE}}.
	 *
	 * <p>If this {{@code JRE}} is {{@link #UNDEFINED}}, this method returns
	 * {{@code -1}}. If this {{@code JRE}} is {{@link #OTHER}}, this method returns
	 * {{@link Integer#MAX_VALUE}}.
	 *
	 * @return the version of this {{@code JRE}}
	 * @since 5.12
	 * @see Runtime.Version#feature()
	 * @see #currentVersionNumber()
	 */
	@API(status = MAINTAINED, since = "5.13.3")
	public int version() {{
		return this.version;
	}}

	/**
	 * @return {{@code true}} if <em>this</em> {{@code JRE}} is known to be the
	 * Java Runtime Environment version for the currently executing JVM or if
	 * the version is {{@link #OTHER}} or {{@link #UNDEFINED}}
	 *
	 * @see #currentJre()
	 * @see #currentVersionNumber()
	 */
	public boolean isCurrentVersion() {{
		return this == CURRENT_JRE;
	}}

	/**
	 * @return the {{@link JRE}} for the currently executing JVM, potentially
	 * {{@link #OTHER}} or {{@link #UNDEFINED}}
	 *
	 * @since 5.7
	 * @see #currentVersionNumber()
	 * @deprecated in favor of {{@link #currentJre()}}
	 */
	@API(status = DEPRECATED, since = "5.12")
	@Deprecated
	public static JRE currentVersion() {{
		return currentJre();
	}}

	/**
	 * @return the {{@link JRE}} for the currently executing JVM, potentially
	 * {{@link #OTHER}} or {{@link #UNDEFINED}}
	 *
	 * @since 5.12
	 * @see #currentVersionNumber()
	 */
	@API(status = STABLE, since = "5.12")
	public static JRE currentJre() {{
		return CURRENT_JRE;
	}}

	/**
	 * @return the version number for the currently executing JVM, or {{@code -1}}
	 * if the current JVM version could not be determined
	 *
	 * @since 5.12
	 * @see Runtime.Version#feature()
	 * @see #currentJre()
	 */
	@API(status = MAINTAINED, since = "5.13.3")
	public static int currentVersionNumber() {{
		return CURRENT_VERSION;
	}}

	/**
	 * Determine if the supplied version number is considered to be the current
	 * JRE version.
	 *
	 * <p>Returns {{@code true}} if any of the following is {{@code true}}.
	 *
	 * <ul>
	 * <li>The supplied version number is known to be the Java Runtime Environment
	 * version for the currently executing JVM.</li>
	 * <li>The supplied version number is {{@link Integer#MAX_VALUE}} and the current
	 * {{@code JRE}} is {{@link JRE#OTHER OTHER}}.</li>
	 * <li>The supplied version number is {{@code -1}} and the current {{@code JRE}}
	 * is {{@link JRE#UNDEFINED UNDEFINED}}.</li>
	 * </ul>
	 *
	 * @return {{@code true}} if the supplied version number is considered to be
	 * the current JRE version
	 * @since 5.12
	 * @see Runtime.Version#feature()
	 * @see #isCurrentVersion()
	 * @see #currentJre()
	 */
	@API(status = MAINTAINED, since = "5.13.3")
	public static boolean isCurrentVersion(int version) {{
		return (version == CURRENT_VERSION) || (version == JRE.currentJre().version);
	}}

	static boolean isCurrentVersionWithinRange(int min, int max) {{
		return CURRENT_VERSION >= min && CURRENT_VERSION <= max;
	}}

}}
""".format(header=header, see=see, constants="\n\n".join(constants), other=other, cases=cases)
    return body


def pom(group, artifact, version, deps):
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<project xmlns="http://maven.apache.org/POM/4.0.0">',
        "  <modelVersion>4.0.0</modelVersion>",
        "  <parent>",
        "    <groupId>org.junit</groupId>",
        "    <artifactId>junit5</artifactId>",
        "    <version>{0}</version>".format(JUPITER),
        "  </parent>",
        "  <groupId>{0}</groupId>".format(group),
        "  <artifactId>{0}</artifactId>".format(artifact),
        "  <version>{0}</version>".format(version),
        "  <name>{0}</name>".format(artifact),
    ]
    if deps:
        lines.append("  <dependencies>")
        for dep in deps:
            lines.append("    <dependency>")
            lines.append("      <groupId>{0}</groupId>".format(dep[0]))
            lines.append("      <artifactId>{0}</artifactId>".format(dep[1]))
            lines.append("      <version>{0}</version>".format(dep[2]))
            if len(dep) > 3 and dep[3]:
                lines.append("      <scope>{0}</scope>".format(dep[3]))
            if len(dep) > 4 and dep[4]:
                lines.append("      <optional>true</optional>")
            lines.append("    </dependency>")
        lines.append("  </dependencies>")
    lines.append("</project>")
    return "\n".join(lines) + "\n"


PLATFORM = "%{platform_ver}"
JUPITER = "%{version}"

header = Path("gradle/config/spotless/eclipse-public-license-2.0.java").read_text(encoding="utf-8").strip() + "\n"
jres = parse_jres(Path("gradle/base/code-generator-model/src/main/resources/jre.yaml"))
generated = render_jre(jres, header)
if "JAVA_26(26)" not in generated or "UNDEFINED(-1)" not in generated:
    raise SystemExit("JRE.java generator missed constants")
jre_path = Path("junit-jupiter-api/src/main/java/org/junit/jupiter/api/condition/JRE.java")
jre_path.parent.mkdir(parents=True, exist_ok=True)
jre_path.write_text(generated, encoding="utf-8")

parent = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.junit</groupId>
  <artifactId>junit5</artifactId>
  <version>{jupiter}</version>
  <packaging>pom</packaging>
  <name>JUnit 5</name>
  <properties>
    <maven.compiler.release>8</maven.compiler.release>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
  </properties>
  <modules>
    <module>junit-platform-commons</module>
    <module>junit-platform-engine</module>
    <module>junit-platform-launcher</module>
    <module>junit-jupiter-api</module>
    <module>junit-jupiter-engine</module>
    <module>junit-vintage-engine</module>
  </modules>
</project>
""".format(jupiter=JUPITER)
Path("pom.xml").write_text(parent, encoding="utf-8")
provided = "provided"
Path("junit-platform-commons/pom.xml").write_text(pom(
    "org.junit.platform", "junit-platform-commons", PLATFORM,
    [("org.apiguardian", "apiguardian-api", "1.1.2", provided)],
), encoding="utf-8")
Path("junit-platform-engine/pom.xml").write_text(pom(
    "org.junit.platform", "junit-platform-engine", PLATFORM,
    [
        ("org.junit.platform", "junit-platform-commons", PLATFORM, None, True),
        ("org.opentest4j", "opentest4j", "1.3.0"),
        ("org.apiguardian", "apiguardian-api", "1.1.2", provided),
    ],
), encoding="utf-8")
Path("junit-platform-launcher/pom.xml").write_text(pom(
    "org.junit.platform", "junit-platform-launcher", PLATFORM,
    [
        ("org.junit.platform", "junit-platform-engine", PLATFORM, None, True),
        ("org.apiguardian", "apiguardian-api", "1.1.2", provided),
    ],
), encoding="utf-8")
Path("junit-jupiter-api/pom.xml").write_text(pom(
    "org.junit.jupiter", "junit-jupiter-api", JUPITER,
    [
        ("org.junit.platform", "junit-platform-commons", PLATFORM, None, True),
        ("org.opentest4j", "opentest4j", "1.3.0"),
        ("org.apiguardian", "apiguardian-api", "1.1.2", provided),
    ],
), encoding="utf-8")
Path("junit-jupiter-engine/pom.xml").write_text(pom(
    "org.junit.jupiter", "junit-jupiter-engine", JUPITER,
    [
        ("org.junit.platform", "junit-platform-engine", PLATFORM, None, True),
        ("org.junit.jupiter", "junit-jupiter-api", JUPITER, None, True),
        ("org.apiguardian", "apiguardian-api", "1.1.2", provided),
    ],
), encoding="utf-8")
Path("junit-vintage-engine/pom.xml").write_text(pom(
    "org.junit.vintage", "junit-vintage-engine", JUPITER,
    [
        ("org.junit.platform", "junit-platform-engine", PLATFORM, None, True),
        ("junit", "junit", "4.13.2"),
        ("org.apiguardian", "apiguardian-api", "1.1.2", provided),
    ],
), encoding="utf-8")
PY
# builddep also reads Gradle scripts. The reactor poms are the build.
find . -name '*.gradle' -delete
find . -name '*.gradle.kts' -delete
find . -name 'libs.versions.toml' -delete

%build -p
python - <<'PY'
from pathlib import Path
removed = 0
for path in Path(".").rglob("pom.xml"):
    text = path.read_text(encoding="utf-8")
    count = text.count("<optional>true</optional>")
    if count:
        path.write_text(text.replace("\n      <optional>true</optional>", ""), encoding="utf-8")
        removed += count
if removed != 6:
    raise SystemExit("expected 6 optional markers, removed " + str(removed))
PY

%build -a
echo 'Automatic-Module-Name: org.junit.platform.commons' > manifest-extra.mf
jar ufm junit-platform-commons/target/junit-platform-commons-%{platform_ver}.jar manifest-extra.mf
echo 'Automatic-Module-Name: org.junit.platform.engine' > manifest-extra.mf
jar ufm junit-platform-engine/target/junit-platform-engine-%{platform_ver}.jar manifest-extra.mf
echo 'Automatic-Module-Name: org.junit.platform.launcher' > manifest-extra.mf
jar ufm junit-platform-launcher/target/junit-platform-launcher-%{platform_ver}.jar manifest-extra.mf
echo 'Automatic-Module-Name: org.junit.jupiter.api' > manifest-extra.mf
jar ufm junit-jupiter-api/target/junit-jupiter-api-%{version}.jar manifest-extra.mf
echo 'Automatic-Module-Name: org.junit.jupiter.engine' > manifest-extra.mf
jar ufm junit-jupiter-engine/target/junit-jupiter-engine-%{version}.jar manifest-extra.mf
echo 'Automatic-Module-Name: org.junit.vintage.engine' > manifest-extra.mf
jar ufm junit-vintage-engine/target/junit-vintage-engine-%{version}.jar manifest-extra.mf

%files -f .mfiles
%doc LICENSE.md README.md
