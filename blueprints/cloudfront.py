from stacker.blueprints.base import Blueprint

from troposphere import cloudfront
from troposphere import NoValue


class S3BackedDistribution(Blueprint):
    VARIABLES = {
        "OriginBucketUrl": {
            "type": str,
            "description": "The domain name for the origin s3 bucket.",
        },
        "CertificateArn": {
            "type": str,
            "description": "ARN of the ACM certificate to use with the "
                           "cloudfront distribution.",
            "default": "",
        },
        "Aliases": {
            "type": list,
            "description": "list of cloudfront distribution aliases.",
            "default": [],
        },
    }

    @property
    def origin_bucket_url(self):
        return self.get_variables()["OriginBucketUrl"]

    @property
    def certificate_arn(self):
        return self.get_variables()["CertificateArn"]

    @property
    def aliases(self):
        return self.get_variables()["Aliases"] or NoValue

    def create_distribution(self):
        t = self.template

        s3_origin = cloudfront.Origin(
            DomainName=self.origin_bucket_url,
            Id="s3",
            CustomOriginConfig=cloudfront.CustomOrigin(
                HTTPPort=80,
                HTTPSPort=443,
                OriginProtocolPolicy="http-only"
            ),
        )

        default_behavior = cloudfront.DefaultCacheBehavior(
            AllowedMethods=["GET", "HEAD"],
            CachedMethods=["GET", "HEAD"],
            ViewerProtocolPolicy="redirect-to-https",
            ForwardedValues=cloudfront.ForwardedValues(
                QueryString=True,
                Cookies=cloudfront.Cookies(
                    Forward="none"
                )
            ),
            MinTTL=0,
            MaxTTL=31536000,
            DefaultTTL=86400,
            SmoothStreaming=False,
            TargetOriginId="s3",
        )

        viewer_certificate = NoValue
        if self.certificate_arn:
            viewer_certificate = cloudfront.ViewerCertificate(
                AcmCertificateArn=self.certificate_arn,
                SslSupportMethod="sni-only",
            )

        config = cloudfront.DistributionConfig(
            Aliases=self.aliases,
            DefaultCacheBehavior=default_behavior,
            Comment="%s" % self.origin_bucket_url,
            Enabled=True,
            PriceClass="PriceClass_All",
            ViewerCertificate=viewer_certificate,
            Origins=[s3_origin],
        )

        self.distribution = t.add_resource(
            cloudfront.Distribution(
                "Distribution",
                DistributionConfig=config,
            )
        )

        self.add_output("DistributionId", self.distribution.Ref())
        self.add_output(
            "DomainName",
            self.distribution.GetAtt("DomainName")
        )

    def create_template(self):
        self.create_distribution()
